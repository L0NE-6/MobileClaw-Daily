import contextlib
import io
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import mobileclaw_daily


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error
        self.text = json.dumps(payload, ensure_ascii=False) if payload else ""

    def json(self):
        if self.json_error is not None:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.headers = {}
        self.trust_env = True
        self.closed = False

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected GET")
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected POST")
        return self.responses.pop(0)

    def close(self):
        self.closed = True


class SessionFactory:
    def __init__(self, responses):
        self.responses = [list(item) for item in responses]
        self.sessions = []

    def __call__(self):
        session = FakeSession(self.responses.pop(0))
        self.sessions.append(session)
        return session


class MobileClawDailyTests(unittest.TestCase):
    def test_unclaimed_account_claims_and_reads_back(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "status": "unclaimed",
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"success": True},
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimed": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"balance": 1000000},
                        }
                    ),
                ]
            ]
        )

        result = mobileclaw_daily.check_account(
            {
                "note": "account_1",
                "kind": "bearer",
                "value": "token-secret-one",
            },
            base_url="https://example.test",
            session_factory=factory,
        )

        self.assertEqual("CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertEqual(1000000, result["credits"])
        self.assertNotIn(
            "token-secret-one",
            json.dumps(result, ensure_ascii=False),
        )
        self.assertTrue(factory.sessions[0].closed)
        calls = factory.sessions[0].calls
        self.assertEqual(["POST", "POST", "POST", "GET"], [c[0] for c in calls])
        self.assertEqual(
            "https://example.test" + mobileclaw_daily.STATUS_PATH,
            calls[0][1],
        )
        self.assertEqual(
            {"activityCodes": ["1003"]},
            calls[0][2]["json"],
        )
        self.assertEqual(
            {"activityCode": "1003"},
            calls[1][2]["json"],
        )
        self.assertEqual(
            "https://example.test" + mobileclaw_daily.CREDITS_PATH,
            calls[3][1],
        )
        self.assertEqual(
            "Bearer token-secret-one",
            calls[0][2]["headers"]["Authorization"],
        )
        self.assertEqual(
            mobileclaw_daily.SERVICE_VERSION,
            calls[0][2]["headers"]["service-version"],
        )

    def test_already_claimed_skips_claim_and_reads_credits(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimed": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"balance": 2500000},
                        }
                    ),
                ]
            ]
        )

        result = mobileclaw_daily.check_account(
            {
                "note": "account_1",
                "kind": "bearer",
                "value": "token-already",
            },
            base_url="https://example.test",
            session_factory=factory,
        )

        self.assertEqual("ALREADY_CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertTrue(result["claimed"])
        self.assertEqual(2500000, result["credits"])
        self.assertEqual(
            ["POST", "GET"],
            [call[0] for call in factory.sessions[0].calls],
        )

    def test_claim_receipt_confirms_success_when_status_readback_lags(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimable": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": [
                                {
                                    "activityCode": "1003",
                                    "claimStatus": "CLAIMED",
                                    "receivedTokenAmount": 1000000,
                                    "consecutiveDays": 1,
                                }
                            ],
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimable": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"remainTokens": 1000000},
                        }
                    ),
                ]
            ]
        )

        result = mobileclaw_daily.check_account(
            {
                "note": "account_1",
                "kind": "bearer",
                "value": "token-receipt",
            },
            base_url="https://example.test",
            session_factory=factory,
        )

        self.assertEqual("CLAIMED", result["result"])
        self.assertTrue(result["ok"])
        self.assertTrue(result["claimed"])
        self.assertEqual(1000000, result["credits"])
        self.assertIn("claim receipt confirmed", result["message"])

    def test_api_failure_is_reported_without_secret(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        status_code=500,
                        payload={
                            "code": 500,
                            "message": "server rejected token-failure",
                        },
                    )
                ]
            ]
        )

        result = mobileclaw_daily.check_account(
            {
                "note": "account_1",
                "kind": "bearer",
                "value": "token-failure",
            },
            base_url="https://example.test",
            session_factory=factory,
        )

        self.assertEqual("HTTP_ERROR", result["result"])
        self.assertFalse(result["ok"])
        self.assertEqual(500, result["http_status"])
        self.assertNotIn(
            "token-failure",
            json.dumps(result, ensure_ascii=False),
        )
        self.assertIn("[REDACTED]", result["message"])

    def test_multi_account_parsing_isolation_and_redaction(self):
        accounts = mobileclaw_daily.load_accounts(
            {
                "MOBILECLAW_TOKENS": (
                    "Bearer token-one,\n"
                    "Cookie: sessionid=secret-two; theme=dark"
                ),
                "MOBILECLAW_BASE_URL": "https://example.test/",
            }
        )
        self.assertEqual(2, len(accounts))
        self.assertEqual("bearer", accounts[0]["kind"])
        self.assertEqual("cookie", accounts[1]["kind"])
        self.assertEqual(
            "https://example.test",
            mobileclaw_daily.resolve_base_url(
                {"MOBILECLAW_BASE_URL": "https://example.test/"}
            ),
        )

        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimable": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"success": True},
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimed": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"balance": 10},
                        }
                    ),
                ],
                [
                    FakeResponse(
                        status_code=401,
                        payload={"message": "expired"},
                    )
                ],
            ]
        )
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            results = mobileclaw_daily.run_accounts(
                accounts,
                base_url="https://example.test",
                session_factory=factory,
            )

        self.assertEqual(2, len(results))
        self.assertEqual("CLAIMED", results[0]["result"])
        self.assertEqual("AUTH_EXPIRED", results[1]["result"])
        self.assertIsNot(factory.sessions[0], factory.sessions[1])
        self.assertTrue(all(session.closed for session in factory.sessions))
        self.assertEqual(
            "Bearer token-one",
            factory.sessions[0].calls[0][2]["headers"]["Authorization"],
        )
        self.assertEqual(
            "sessionid=secret-two; theme=dark",
            factory.sessions[1].calls[0][2]["headers"]["Cookie"],
        )

        rendered = output.getvalue()
        self.assertNotIn("token-one", rendered)
        self.assertNotIn("secret-two", rendered)
        lines = [
            json.loads(line)
            for line in rendered.splitlines()
            if line.strip()
        ]
        self.assertEqual(2, len(lines))

    def test_single_account_env_and_remain_tokens_are_supported(self):
        accounts = mobileclaw_daily.load_accounts(
            {"MOBILECLAW_TOKEN": "single-token"}
        )
        self.assertEqual(1, len(accounts))
        self.assertEqual("bearer", accounts[0]["kind"])
        self.assertEqual("single-token", accounts[0]["value"])
        self.assertEqual(
            "https://zhenze-huhehaote.cmecloud.cn",
            mobileclaw_daily.resolve_base_url({}),
        )
        self.assertEqual(
            123456,
            mobileclaw_daily.parse_credits(
                {"data": {"remainTokens": 123456}}
            ),
        )

    def test_real_name_error_is_classified_as_ineligible(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        payload={
                            "success": False,
                            "code": "C403001",
                            "message": "upstream detail",
                        }
                    )
                ]
            ]
        )

        result = mobileclaw_daily.check_account(
            {
                "note": "account_1",
                "kind": "bearer",
                "value": "token-ineligible",
            },
            base_url="https://example.test",
            session_factory=factory,
        )

        self.assertEqual("INELIGIBLE", result["result"])
        self.assertFalse(result["ok"])
        self.assertIn("实名认证", result["message"])

    def test_main_summary_is_last_line_and_has_run_all_fields(self):
        factory = SessionFactory(
            [
                [
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {
                                "activityCode": "1003",
                                "claimed": True,
                            },
                        }
                    ),
                    FakeResponse(
                        payload={
                            "code": 0,
                            "data": {"balance": 7},
                        }
                    ),
                ]
            ]
        )
        output = []

        code = mobileclaw_daily.main(
            [],
            env={"MOBILECLAW_TOKENS": "token-main"},
            session_factory=factory,
            output=output.append,
        )

        self.assertEqual(0, code)
        summary = output[-1]
        self.assertEqual("mobileclaw", summary["provider"])
        self.assertEqual(1, summary["accounts"])
        self.assertEqual(1, summary["success"])
        self.assertEqual(0, summary["failed"])
        self.assertEqual(1, len(summary["results"]))
        self.assertNotIn(
            "token-main",
            json.dumps(output, ensure_ascii=False),
        )

    def test_config_error_still_ends_with_summary(self):
        output = []
        code = mobileclaw_daily.main(
            [],
            env={},
            session_factory=SessionFactory([]),
            output=output.append,
        )

        self.assertEqual(2, code)
        self.assertEqual("CONFIG_ERROR", output[0]["result"])
        self.assertEqual("mobileclaw", output[-1]["provider"])
        self.assertEqual(1, output[-1]["failed"])


if __name__ == "__main__":
    unittest.main()
