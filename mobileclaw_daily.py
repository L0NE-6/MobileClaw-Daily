#!/usr/bin/env python3
"""MobileClaw daily token welfare claimer.

Environment:
    MOBILECLAW_TOKENS
        Comma or newline separated credentials. A value without "=" is sent
        as an Authorization Bearer token. A value containing "=" is sent as a
        Cookie header.
    MOBILECLAW_TOKEN
        Single-account credential used when MOBILECLAW_TOKENS is empty.
    MOBILECLAW_BASE_URL
        Optional base URL override. The default is centralized below.

The script prints one JSON object per account followed by a final summary
object. The summary is the last line so run_all.py can parse it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence
from urllib.parse import urlparse

import requests


PROVIDER = "mobileclaw"
DEFAULT_BASE_URL = "https://zhenze-huhehaote.cmecloud.cn"
BASE_URL_ENV = "MOBILECLAW_BASE_URL"
TOKENS_ENV = "MOBILECLAW_TOKENS"
TOKEN_ENV = "MOBILECLAW_TOKEN"
ACTIVITY_CODE = "1003"
STATUS_PATH = "/desktop/manager/token-welfare/status"
CLAIM_PATH = "/desktop/manager/token-welfare/claim"
CREDITS_PATH = "/credits/v2/exp-credit"
REQUEST_TIMEOUT = 20
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "MobileClaw/1.9.8 Chrome/136.0.7103.177 "
    "Electron/36.9.5 Safari/537.36"
)
SERVICE_VERSION = "2.6.1"

BASE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT,
    "service-version": SERVICE_VERSION,
}

INELIGIBLE_CODES = {
    "C404003": "当前用户未注册，请先在移动云完成注册",
    "C403001": "当前用户未完成实名认证",
    "C401003": "实名认证审核中，审核通过后才能领取",
}


class ConfigError(ValueError):
    """Configuration or account input error."""


class APIError(RuntimeError):
    """A classified API failure."""

    def __init__(
        self,
        result: str,
        message: str,
        *,
        http_status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.result = result
        self.message = message
        self.http_status = http_status


def emit(payload: Mapping[str, Any]) -> None:
    """Print one compact JSON line."""
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        flush=True,
    )


def _redact(value: Any, secrets: Sequence[str]) -> str:
    text = str(value)
    unique = []
    for secret in secrets:
        secret = str(secret or "")
        if secret and secret not in unique:
            unique.append(secret)
    for secret in sorted(unique, key=len, reverse=True):
        text = text.replace(secret, "[REDACTED]")
    return text


def _credential_value(account: Mapping[str, Any]) -> tuple[str, str]:
    """Return (kind, value) for a loaded or caller-supplied account."""
    kind = str(account.get("kind", "") or "").strip().lower()
    if kind in ("bearer", "token", "authorization"):
        value = account.get("value", account.get("token", ""))
        return "bearer", str(value or "").strip()
    if kind == "cookie":
        value = account.get("value", account.get("cookie", ""))
        return "cookie", str(value or "").strip()

    # Accept simple dictionaries used by callers and tests.
    if account.get("cookie"):
        return "cookie", str(account.get("cookie") or "").strip()
    if account.get("token"):
        return "bearer", str(account.get("token") or "").strip()
    if account.get("authorization"):
        return "bearer", str(account.get("authorization") or "").strip()
    value = str(account.get("value", "") or "").strip()
    return ("cookie" if "=" in value else "bearer"), value


def _credential_secrets(account: Mapping[str, Any]) -> list[str]:
    kind, value = _credential_value(account)
    secrets = [value]
    if kind == "bearer":
        token = value
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        secrets.extend([token, "Bearer " + token])
    else:
        for part in value.split(";"):
            part = part.strip()
            if not part:
                continue
            secrets.append(part)
            if "=" in part:
                secrets.append(part.split("=", 1)[1].strip())
    return secrets


def _auth_headers(
    account: Mapping[str, Any],
    base_url: str,
) -> dict[str, str]:
    kind, value = _credential_value(account)
    if not value:
        raise ConfigError("empty credential")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        "service-version": SERVICE_VERSION,
        "Origin": base_url,
        "Referer": base_url + "/",
    }
    if kind == "cookie":
        headers["Cookie"] = value
        return headers

    token = value
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if not token:
        raise ConfigError("empty bearer token")
    headers["Authorization"] = "Bearer " + token
    return headers


def _normalize_base_url(base_url: str) -> str:
    base_url = str(base_url or "").strip().rstrip("/")
    parsed = urlparse(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ConfigError("MOBILECLAW_BASE_URL must be an http(s) URL")
    return base_url


def resolve_base_url(env: Optional[Mapping[str, str]] = None) -> str:
    """Resolve and validate the centralized base URL."""
    values = os.environ if env is None else env
    base_url = str(values.get(BASE_URL_ENV, "") or "").strip()
    if not base_url:
        base_url = DEFAULT_BASE_URL
    return _normalize_base_url(base_url)


def load_accounts(
    env: Optional[Mapping[str, str]] = None,
) -> list[dict[str, str]]:
    """Parse MOBILECLAW_TOKENS without exposing credential values."""
    values = os.environ if env is None else env
    raw = str(values.get(TOKENS_ENV, "") or "").strip()
    if not raw:
        raw = str(values.get(TOKEN_ENV, "") or "").strip()
    if not raw:
        raise ConfigError(
            "MOBILECLAW_TOKENS or MOBILECLAW_TOKEN is not configured"
        )

    parts = [part.strip() for part in re.split(r"[,\r\n]+", raw)]
    parts = [part for part in parts if part]
    if not parts:
        raise ConfigError("MOBILECLAW_TOKENS contains no accounts")

    accounts: list[dict[str, str]] = []
    for index, part in enumerate(parts, 1):
        lowered = part.lower()
        if lowered.startswith("authorization:"):
            value = part.split(":", 1)[1].strip()
            kind = "bearer"
        elif lowered.startswith("cookie:"):
            value = part.split(":", 1)[1].strip()
            kind = "cookie"
        elif lowered.startswith("bearer "):
            value = part
            kind = "bearer"
        elif "=" in part:
            value = part
            kind = "cookie"
        else:
            value = part
            kind = "bearer"
        if not value:
            raise ConfigError("account %d has an empty credential" % index)
        accounts.append(
            {
                "note": "account_%d" % index,
                "kind": kind,
                "value": value,
            }
        )
    return accounts


def make_session() -> requests.Session:
    """Create an isolated requests session."""
    session = requests.Session()
    session.trust_env = False
    session.headers.update(BASE_HEADERS)
    return session


def _payload_message(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    for key in ("message", "msg", "detail", "errorMessage", "error"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            nested = _payload_message(value)
            if nested:
                return nested
        elif value not in (None, "", False):
            return str(value)
    return ""


def _business_error(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    if payload.get("success") is False:
        return _payload_message(payload) or "business request failed"

    error = payload.get("error")
    if error not in (None, "", False, {}, []):
        return _payload_message(payload) or str(error)

    status = str(payload.get("status", "") or "").strip().lower()
    if status in ("error", "failed", "failure"):
        return _payload_message(payload) or "business request failed"

    code = payload.get("code")
    if code is not None and not isinstance(code, bool):
        try:
            numeric_code = int(code)
        except (TypeError, ValueError):
            numeric_code = None
        if numeric_code is not None and (
            numeric_code in (400, 401, 403, 404, 409, 429)
            or numeric_code >= 500
        ):
            return _payload_message(payload) or "business request failed"
    return ""


def _business_code(payload: Any) -> str:
    if not isinstance(payload, Mapping):
        return ""
    for key in ("code", "errno", "errorCode", "error_code"):
        value = payload.get(key)
        if value not in (None, "", False):
            return str(value)
    error = payload.get("error")
    if isinstance(error, Mapping):
        return _business_code(error)
    return ""


def _response_text(response: Any) -> str:
    text = getattr(response, "text", "")
    if text:
        return str(text)
    try:
        payload = response.json()
    except Exception:
        return ""
    return json.dumps(payload, ensure_ascii=False, default=str)


def _call_api(
    session: requests.Session,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    json_body: Optional[Mapping[str, Any]],
    secrets: Sequence[str],
) -> tuple[Any, int]:
    try:
        if method == "GET":
            response = session.get(
                url,
                headers=dict(headers),
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
            )
        else:
            response = session.post(
                url,
                headers=dict(headers),
                json=dict(json_body or {}),
                timeout=REQUEST_TIMEOUT,
                allow_redirects=False,
            )
    except requests.RequestException as exc:
        raise APIError(
            "NETWORK_ERROR",
            "network request failed: %s" % _redact(exc, secrets),
        ) from exc
    except Exception as exc:
        raise APIError(
            "NETWORK_ERROR",
            "network request failed: %s" % _redact(exc, secrets),
        ) from exc

    try:
        status_code = int(getattr(response, "status_code", 0) or 0)
    except (TypeError, ValueError):
        status_code = 0
    if status_code in (401, 403):
        raise APIError(
            "AUTH_EXPIRED",
            "credential is invalid or expired (HTTP %d)" % status_code,
            http_status=status_code,
        )
    if status_code == 429:
        raise APIError(
            "RATE_LIMITED",
            "request was rate limited (HTTP %d)" % status_code,
            http_status=status_code,
        )
    if 300 <= status_code < 400:
        raise APIError(
            "REDIRECT",
            "request was redirected (HTTP %d)" % status_code,
            http_status=status_code,
        )
    if not 200 <= status_code < 300:
        detail = _redact(_response_text(response), secrets)
        message = "API request failed (HTTP %d)" % status_code
        if detail:
            message += ": " + detail[:240]
        raise APIError(
            "HTTP_ERROR",
            message,
            http_status=status_code,
        )

    try:
        payload = response.json()
    except Exception as exc:
        raise APIError(
            "INVALID_JSON",
            "API response is not JSON: %s" % _redact(exc, secrets),
            http_status=status_code,
        ) from exc
    if not isinstance(payload, (dict, list)):
        raise APIError(
            "INVALID_RESPONSE",
            "API response is not a JSON object or array",
            http_status=status_code,
        )

    business_error = _business_error(payload)
    if business_error:
        code = _business_code(payload)
        if code in INELIGIBLE_CODES:
            raise APIError(
                "INELIGIBLE",
                INELIGIBLE_CODES[code],
                http_status=status_code,
            )
        raise APIError(
            "BUSINESS_ERROR",
            _redact(business_error, secrets),
            http_status=status_code,
        )
    return payload, status_code


def _normalized_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _walk_dicts(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _find_activity(payload: Any, code: str = ACTIVITY_CODE) -> Optional[Mapping[str, Any]]:
    if isinstance(payload, Mapping):
        activity_code = payload.get("activityCode")
        if activity_code is None:
            activity_code = payload.get("activity_code")
        if str(activity_code) == str(code):
            return payload
        if code in payload and isinstance(payload.get(code), Mapping):
            return payload[code]
        for child in payload.values():
            found = _find_activity(child, code)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for child in payload:
            found = _find_activity(child, code)
            if found is not None:
                return found
    return None


def _status_scope(payload: Any) -> Any:
    activity = _find_activity(payload)
    if activity is not None:
        return activity
    if isinstance(payload, Mapping):
        data = payload.get("data", payload)
        if isinstance(data, Mapping):
            for key in ("activities", "activityList", "welfareList", "records"):
                value = data.get(key)
                if isinstance(value, list) and len(value) == 1:
                    return value[0]
            return data
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        return payload
    if isinstance(payload, list) and len(payload) == 1:
        return payload[0]
    return payload


def _truthy_flag(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in ("true", "1", "yes", "y"):
        return True
    if text in ("false", "0", "no", "n"):
        return False
    return None


def _status_state(payload: Any) -> tuple[str, str]:
    """Return (claimed|claimable|unknown, short reason)."""
    scope = _status_scope(payload)
    claimed_keys = {
        "claimed",
        "isclaimed",
        "received",
        "isreceived",
        "hasclaimed",
        "hasreceived",
        "claimedtoday",
        "isclaimedtoday",
        "receivedtoday",
    }
    claimable_keys = {
        "claimable",
        "isclaimable",
        "canclaim",
        "iscanclaim",
        "available",
        "isavailable",
        "canreceive",
        "iscanreceive",
    }
    status_keys = {
        "claimstatus",
        "status",
        "state",
        "receivestatus",
        "welfarestatus",
        "activitystatus",
    }

    status_values: list[tuple[str, Any]] = []
    saw_claimable_true = False
    saw_claimed_false = False
    for item in _walk_dicts(scope):
        for key, value in item.items():
            normalized = _normalized_key(key)
            if normalized in claimed_keys:
                flag = _truthy_flag(value)
                if flag is True:
                    return "claimed", "claimed flag"
                if flag is False:
                    saw_claimed_false = True
            elif normalized in claimable_keys:
                flag = _truthy_flag(value)
                if flag is True:
                    saw_claimable_true = True
            elif normalized in status_keys and value is not None:
                status_values.append((normalized, value))

    if saw_claimable_true or saw_claimed_false:
        return "claimable", "claimable flag"

    for key, value in status_values:
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            number = int(value)
            if key in ("claimstatus", "receivestatus"):
                if number in (1, 2):
                    return "claimed", "status code"
                if number == 0:
                    return "claimable", "status code"
            elif key in ("status", "state", "activitystatus"):
                if number == 0:
                    return "claimable", "status code"
                if number in (2, 3):
                    return "claimed", "status code"
            continue

        text = re.sub(r"[\s_-]+", "", str(value).lower())
        if not text:
            continue
        if any(
            marker in text
            for marker in (
                "claimable",
                "available",
                "unclaimed",
                "notclaimed",
                "notreceived",
                "notyet",
                "canclaim",
                "toclaim",
                "pending",
                "可领取",
                "待领取",
                "未领取",
            )
        ):
            return "claimable", "status text"
        if any(
            marker in text
            for marker in (
                "alreadyclaimed",
                "alreadyreceived",
                "claimed",
                "received",
                "finished",
                "done",
                "已领取",
                "已领",
                "领取成功",
                "已完成",
            )
        ):
            return "claimed", "status text"
    return "unknown", "status is not recognized"


def _looks_already_claimed(message: str) -> bool:
    text = str(message or "").lower()
    return any(
        marker in text
        for marker in (
            "already",
            "duplicate",
            "repeated",
            "已领取",
            "已领",
            "领取过",
            "重复领取",
        )
    )


def _claim_already(payload: Any) -> bool:
    for item in _walk_dicts(payload):
        for key, value in item.items():
            normalized = _normalized_key(key)
            if normalized in (
                "alreadyclaimed",
                "isalreadyclaimed",
                "alreadyreceived",
                "isalreadyreceived",
            ) and _truthy_flag(value) is True:
                return True
    return _looks_already_claimed(_payload_message(payload))


def _optional_number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return int(number) if number.is_integer() else number


def parse_credits(payload: Any) -> Optional[float]:
    """Extract the first plausible balance from a credits response."""
    priority = (
        "remaintokens",
        "balance",
        "credits",
        "credit",
        "expcredit",
        "expcredits",
        "available",
        "availablecredits",
        "remaining",
        "remainingcredits",
        "total",
        "totalcredits",
        "amount",
    )
    for wanted in priority:
        for item in _walk_dicts(payload):
            for key, value in item.items():
                if _normalized_key(key) != wanted:
                    continue
                number = _optional_number(value)
                if number is not None:
                    return number
    if isinstance(payload, Mapping):
        number = _optional_number(payload.get("data"))
        if number is not None:
            return number
    return None


def _result(
    account: Mapping[str, Any],
    result: str,
    ok: bool,
    message: str,
    *,
    http_status: Optional[int] = None,
    claimed: bool = False,
    credits: Optional[float] = None,
    before_state: str = "",
    after_state: str = "",
) -> dict[str, Any]:
    return {
        "account": str(account.get("note", "")),
        "provider": PROVIDER,
        "result": result,
        "ok": ok,
        "message": message,
        "http_status": http_status,
        "activity_code": ACTIVITY_CODE,
        "claimed": claimed,
        "credits": credits,
        "before_state": before_state,
        "after_state": after_state,
    }


def _read_credits(
    session: requests.Session,
    base_url: str,
    headers: Mapping[str, str],
    secrets: Sequence[str],
) -> tuple[Optional[float], int]:
    payload, status_code = _call_api(
        session,
        "GET",
        base_url + CREDITS_PATH,
        headers=headers,
        json_body=None,
        secrets=secrets,
    )
    credits = parse_credits(payload)
    if credits is None:
        raise APIError(
            "CREDITS_UNRECOGNIZED",
            "credits response did not contain a balance",
            http_status=status_code,
        )
    return credits, status_code


def _read_status(
    session: requests.Session,
    base_url: str,
    headers: Mapping[str, str],
    secrets: Sequence[str],
) -> tuple[Any, int]:
    return _call_api(
        session,
        "POST",
        base_url + STATUS_PATH,
        headers=headers,
        json_body={"activityCodes": [ACTIVITY_CODE]},
        secrets=secrets,
    )


def _readback_after_claim(
    session: requests.Session,
    base_url: str,
    headers: Mapping[str, str],
    secrets: Sequence[str],
    *,
    account: Mapping[str, Any],
    before_state: str,
    claim_payload: Any,
) -> dict[str, Any]:
    claim_state, _ = _status_state(claim_payload)
    after_payload, after_status = _read_status(
        session,
        base_url,
        headers,
        secrets,
    )
    after_state, _ = _status_state(after_payload)
    credits, _ = _read_credits(
        session,
        base_url,
        headers,
        secrets,
    )
    if after_state == "claimed":
        return _result(
            account,
            "CLAIMED",
            True,
            "claimed activity %s; credits=%s" % (ACTIVITY_CODE, credits),
            http_status=after_status,
            claimed=True,
            credits=credits,
            before_state=before_state,
            after_state=after_state,
        )
    if claim_state == "claimed":
        return _result(
            account,
            "CLAIMED",
            True,
            "claim receipt confirmed activity %s; status readback is %s; "
            "credits=%s" % (ACTIVITY_CODE, after_state, credits),
            http_status=after_status,
            claimed=True,
            credits=credits,
            before_state=before_state,
            after_state=after_state,
        )
    if after_state == "claimable":
        return _result(
            account,
            "CLAIM_NOT_APPLIED",
            False,
            "claim returned success but status is still claimable; credits=%s"
            % credits,
            http_status=after_status,
            credits=credits,
            before_state=before_state,
            after_state=after_state,
        )
    return _result(
        account,
        "READBACK_UNCONFIRMED",
        False,
        "claim status could not be confirmed; credits=%s" % credits,
        http_status=after_status,
        credits=credits,
        before_state=before_state,
        after_state=after_state,
    )


def _readback_already(
    session: requests.Session,
    base_url: str,
    headers: Mapping[str, str],
    secrets: Sequence[str],
    *,
    account: Mapping[str, Any],
    before_state: str,
    http_status: Optional[int],
) -> dict[str, Any]:
    after_payload, after_status = _read_status(
        session,
        base_url,
        headers,
        secrets,
    )
    after_state, _ = _status_state(after_payload)
    credits, _ = _read_credits(
        session,
        base_url,
        headers,
        secrets,
    )
    if after_state != "claimed":
        return _result(
            account,
            "CLAIM_CONFLICT",
            False,
            "claim reported already claimed but status is not confirmed; credits=%s"
            % credits,
            http_status=http_status or after_status,
            credits=credits,
            before_state=before_state,
            after_state=after_state,
        )
    return _result(
        account,
        "ALREADY_CLAIMED",
        True,
        "activity %s was already claimed; credits=%s"
        % (ACTIVITY_CODE, credits),
        http_status=http_status or after_status,
        claimed=True,
        credits=credits,
        before_state=before_state,
        after_state=after_state,
    )


def check_account(
    account: Mapping[str, Any],
    *,
    mode: str = "claim",
    base_url: Optional[str] = None,
    session_factory: Callable[[], requests.Session] = make_session,
) -> dict[str, Any]:
    """Process one account; exceptions are converted to a failure result."""
    try:
        resolved_base_url = _normalize_base_url(base_url or resolve_base_url())
        headers = _auth_headers(account, resolved_base_url)
    except ConfigError as exc:
        return _result(
            account,
            "CONFIG_ERROR",
            False,
            str(exc),
        )

    secrets = _credential_secrets(account)
    session = None
    try:
        session = session_factory()
        if hasattr(session, "trust_env"):
            session.trust_env = False
        if hasattr(session, "headers"):
            session.headers.update(BASE_HEADERS)

        before_payload, before_status = _read_status(
            session,
            resolved_base_url,
            headers,
            secrets,
        )
        before_state, _ = _status_state(before_payload)

        if before_state == "claimed":
            credits, credits_status = _read_credits(
                session,
                resolved_base_url,
                headers,
                secrets,
            )
            return _result(
                account,
                "ALREADY_CLAIMED",
                True,
                "activity %s was already claimed; credits=%s"
                % (ACTIVITY_CODE, credits),
                http_status=before_status or credits_status,
                claimed=True,
                credits=credits,
                before_state=before_state,
                after_state=before_state,
            )

        if before_state != "claimable":
            return _result(
                account,
                "STATUS_UNRECOGNIZED",
                False,
                "activity %s status is not recognized" % ACTIVITY_CODE,
                http_status=before_status,
                before_state=before_state,
                after_state=before_state,
            )

        if mode == "status":
            credits, credits_status = _read_credits(
                session,
                resolved_base_url,
                headers,
                secrets,
            )
            return _result(
                account,
                "AVAILABLE",
                True,
                "activity %s is claimable; credits=%s"
                % (ACTIVITY_CODE, credits),
                http_status=before_status or credits_status,
                credits=credits,
                before_state=before_state,
                after_state=before_state,
            )

        try:
            claim_payload, claim_status = _call_api(
                session,
                "POST",
                resolved_base_url + CLAIM_PATH,
                headers=headers,
                json_body={"activityCode": ACTIVITY_CODE},
                secrets=secrets,
            )
        except APIError as exc:
            if (
                exc.result in ("BUSINESS_ERROR", "HTTP_ERROR")
                and _looks_already_claimed(exc.message)
            ):
                try:
                    return _readback_already(
                        session,
                        resolved_base_url,
                        headers,
                        secrets,
                        account=account,
                        before_state=before_state,
                        http_status=exc.http_status,
                    )
                except APIError as readback_error:
                    return _result(
                        account,
                        readback_error.result,
                        False,
                        readback_error.message,
                        http_status=readback_error.http_status,
                        before_state=before_state,
                    )
            return _result(
                account,
                exc.result,
                False,
                exc.message,
                http_status=exc.http_status,
                before_state=before_state,
            )

        if _claim_already(claim_payload):
            try:
                result = _readback_already(
                    session,
                    resolved_base_url,
                    headers,
                    secrets,
                    account=account,
                    before_state=before_state,
                    http_status=claim_status,
                )
                return result
            except APIError as readback_error:
                return _result(
                    account,
                    readback_error.result,
                    False,
                    readback_error.message,
                    http_status=readback_error.http_status,
                    before_state=before_state,
                )

        try:
            result = _readback_after_claim(
                session,
                resolved_base_url,
                headers,
                secrets,
                account=account,
                before_state=before_state,
                claim_payload=claim_payload,
            )
        except APIError as readback_error:
            return _result(
                account,
                readback_error.result,
                False,
                readback_error.message,
                http_status=readback_error.http_status,
                before_state=before_state,
            )
        return result
    except APIError as exc:
        return _result(
            account,
            exc.result,
            False,
            exc.message,
            http_status=exc.http_status,
        )
    except ConfigError as exc:
        return _result(account, "CONFIG_ERROR", False, str(exc))
    except Exception as exc:
        return _result(
            account,
            "UNEXPECTED_ERROR",
            False,
            "unexpected error: %s" % _redact(exc, secrets),
        )
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


def run_accounts(
    accounts: Sequence[Mapping[str, Any]],
    *,
    mode: str = "claim",
    base_url: Optional[str] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> list[dict[str, Any]]:
    """Process accounts independently and continue after individual failures."""
    resolved_base_url = _normalize_base_url(base_url or resolve_base_url())
    results: list[dict[str, Any]] = []
    for account in accounts:
        result = check_account(
            account,
            mode=mode,
            base_url=resolved_base_url,
            session_factory=session_factory,
        )
        results.append(result)
        output(result)
    return results


def build_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    success = sum(1 for result in results if result.get("ok") is True)
    failed = len(results) - success
    return {
        "provider": PROVIDER,
        "accounts": len(results),
        "success": success,
        "failed": failed,
        "results": [dict(result) for result in results],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Claim MobileClaw daily token welfare for all accounts."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="query status and credits without claiming",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=("status",),
        help=argparse.SUPPRESS,
    )
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> int:
    args = build_parser().parse_args(argv)
    mode = "status" if args.status or args.action == "status" else "claim"
    try:
        accounts = load_accounts(env)
        base_url = resolve_base_url(env)
    except ConfigError as exc:
        result = _result(
            {"note": "config"},
            "CONFIG_ERROR",
            False,
            str(exc),
        )
        summary = build_summary([result])
        output(result)
        output(summary)
        return 2

    results = run_accounts(
        accounts,
        mode=mode,
        base_url=base_url,
        session_factory=session_factory,
        output=output,
    )
    summary = build_summary(results)
    output(summary)
    return 0 if summary["failed"] == 0 else 1


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    _configure_utf8_stdio()
    sys.exit(main())
