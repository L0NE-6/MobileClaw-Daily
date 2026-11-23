<div align="center">

# 🦞 MobileClaw Daily

**Daily MobileClaw token welfare · multi-account claim · status → claim → status / credits**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

> [!IMPORTANT]
> This project is free. Resale, paywalling, paid redeployment, traffic-baiting
> redistribution, author impersonation, and removal of copyright notices are
> prohibited. See [NOTICE.md](../NOTICE.md).

## What It Does

MobileClaw Daily is an original L0NE-6 maintenance project. It checks activity
`1003`, claims the daily token welfare when available, and confirms the result
through server-side status and credits readback.

| Item | Description |
| :--- | :--- |
| Input | `MOBILECLAW_TOKENS` or `MOBILECLAW_TOKEN` |
| Output | Per-account JSON and a final summary JSON |
| Runtime | Python 3.9+ with `requests` |
| Deploy | Windows, Linux, Qinglong, GitHub Actions |
| Success | Final status or a confirmed claim receipt, plus a readable credits balance |

## Protocol Flow

```text
POST status {"activityCodes":["1003"]}
  ├─ claimed   -> GET credits -> ALREADY_CLAIMED
  └─ claimable -> POST claim {"activityCode":"1003"}
                    -> POST status again
                    -> GET credits
                    -> CLAIMED / CLAIM_NOT_APPLIED / READBACK_UNCONFIRMED
```

An HTTP 200 response alone is not success. A successful result must include a
credible final state or claim receipt and a readable credits balance.

## Credentials

`MOBILECLAW_TOKENS` supports comma- or newline-separated values:

```text
Bearer <token>
Authorization: <token>
Cookie: <name>=<value>; <name>=<value>
<token>
```

A value without `=` is treated as a Bearer token. A value containing `=` is
treated as a Cookie. `MOBILECLAW_TOKEN` is used only when
`MOBILECLAW_TOKENS` is empty.

Never commit real tokens, cookies, phone numbers, authentication files, or
runtime reports.

## Eligibility Errors

| Code | Meaning |
| :--- | :--- |
| `C404003` | Account is not registered |
| `C403001` | Real-name verification is incomplete |
| `C401003` | Real-name verification is under review |

These are reported as `INELIGIBLE`; complete the required account action before
running again.

## Local Run

```bash
python -m pip install -r requirements.txt
export MOBILECLAW_TOKEN='<your token or cookie>'
python mobileclaw_daily.py
```

Status only:

```bash
python mobileclaw_daily.py --status
```

## Qinglong

1. Install `requests`.
2. Upload `mobileclaw_daily.py`.
3. Add `MOBILECLAW_TOKENS` or `MOBILECLAW_TOKEN`.
4. Create a scheduled task with `task mobileclaw_daily.py`.
5. Run once per day at a time that matches your account usage.

## GitHub Actions

The included workflow runs tests on every push to `main`. One scheduled run
per day performs tests, claims tokens, and uploads the JSON report artifact.

| Secret | Required | Value |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | Either one | Multi-account tokens or cookies |
| `MOBILECLAW_TOKEN` | Either one | Single-account token or cookie |

The schedule is `17 23 * * *` UTC, which is 07:17 Beijing time. GitHub
schedules are best-effort and may be delayed.

## Success Criteria

- `ALREADY_CLAIMED`: status readback is `claimed` and credits are readable.
- `CLAIMED`: final status is `claimed`, or the claim receipt is `claimed` while
  the final status lag is recorded, and credits are readable.
- `AVAILABLE`: status-only mode confirms `claimable` and reads credits.
- `CLAIM_NOT_APPLIED`, `READBACK_UNCONFIRMED`, and
  `STATUS_UNRECOGNIZED` are failures.

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check mobileclaw_daily.py tests
```

Tests use fake sessions and never contact the live claim service.

## Privacy

No credentials or personal data are stored in this repository. Reports are
redacted, and generated report files are ignored by Git.

## Disclaimer

Use this project for lawful personal automation. Activity rules, eligibility,
interfaces, and balances are controlled by the service provider. Use is at
your own risk.

---

[Back to Chinese README](../README.md) · [Usage policy](../NOTICE.md) · [Donation and Star History](../README.md#star-trail)
