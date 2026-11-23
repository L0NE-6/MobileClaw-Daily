<div align="center">

# 🦞 MobileClaw Daily

**MobileClaw 일일 Token 혜택 · 다중 계정 · status → claim → status / credits 재확인**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

> [!IMPORTANT]
> 이 프로젝트는 무료입니다. 재판매, 유료 패키징, 유료 대행 배포, 유입용 재배포, 작성자 사칭, 저작권 표시 제거를 금지합니다. 자세한 내용은 [NOTICE.md](../NOTICE.md)를 확인하세요.

## 기능

MobileClaw Daily는 L0NE-6이 독자적으로 유지보수하는 단일 파일 스크립트입니다. 활동 `1003`을 확인하고, 받을 수 있으면 claim을 실행한 뒤 서버 status와 credits로 결과를 확인합니다.

| 항목 | 설명 |
| :--- | :--- |
| 입력 | `MOBILECLAW_TOKENS` 또는 `MOBILECLAW_TOKEN` |
| 출력 | 계정별 JSON과 마지막 집계 JSON |
| 실행 환경 | Python 3.9+, `requests`만 필요 |
| 배포 | Windows, Linux, Qinglong, GitHub Actions |
| 성공 | 최종 상태 또는 claim 영수 증거가 확인되고 credits를 읽을 수 있음 |

## 프로토콜 흐름

```text
POST status {"activityCodes":["1003"]}
  ├─ claimed   -> GET credits -> ALREADY_CLAIMED
  └─ claimable -> POST claim {"activityCode":"1003"}
                    -> POST status again
                    -> GET credits
                    -> CLAIMED / CLAIM_NOT_APPLIED / READBACK_UNCONFIRMED
```

HTTP 200만으로는 성공이 아닙니다. 신뢰할 수 있는 최종 상태 또는 claim 영수 증거와 credits 읽기가 필요합니다.

## 자격 증명

`MOBILECLAW_TOKENS`는 쉼표 또는 줄바꿈으로 구분합니다.

```text
Bearer <token>
Authorization: <token>
Cookie: <name>=<value>; <name>=<value>
<token>
```

`=`가 없는 값은 Bearer Token, `=`가 있는 값은 Cookie로 처리합니다. `MOBILECLAW_TOKEN`은 `MOBILECLAW_TOKENS`가 비어 있을 때만 사용합니다.

실제 Token, Cookie, 전화번호, 인증 파일, 실행 보고서를 커밋하지 마세요.

## 자격 오류

| 코드 | 의미 |
| :--- | :--- |
| `C404003` | 계정 미등록 |
| `C403001` | 실명 인증 미완료 |
| `C401003` | 실명 인증 심사 중 |

이 경우 `INELIGIBLE`로 보고됩니다. 필요한 계정 절차를 완료한 뒤 다시 실행하세요.

## 로컬 실행

```bash
python -m pip install -r requirements.txt
export MOBILECLAW_TOKEN='<Token 또는 Cookie>'
python mobileclaw_daily.py
```

상태만 확인:

```bash
python mobileclaw_daily.py --status
```

## Qinglong

1. `requests`를 설치합니다.
2. `mobileclaw_daily.py`를 업로드합니다.
3. `MOBILECLAW_TOKENS` 또는 `MOBILECLAW_TOKEN`을 설정합니다.
4. 예약 작업 명령을 `task mobileclaw_daily.py`로 설정합니다.
5. 계정 규칙에 맞춰 하루 한 번 실행합니다.

## GitHub Actions

`main` push에서는 테스트를 실행합니다. 일일 예약 실행은 테스트 후 혜택을 받고 JSON 보고서 artifact를 업로드합니다.

| Secret | 필수 | 값 |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | 둘 중 하나 | 다중 계정 Token 또는 Cookie |
| `MOBILECLAW_TOKEN` | 둘 중 하나 | 단일 계정 Token 또는 Cookie |

예약은 UTC `17 23 * * *`, 베이징 시간 07:17입니다. GitHub 예약은 지연될 수 있습니다.

## 성공 기준

- `ALREADY_CLAIMED`: status가 `claimed`이고 credits를 읽을 수 있음.
- `CLAIMED`: 최종 status가 `claimed`이거나 claim 영수 증거가 `claimed`이고 상태 지연이 기록되며 credits를 읽을 수 있음.
- `AVAILABLE`: 상태 확인 모드에서 `claimable`을 확인하고 credits를 읽음.
- `CLAIM_NOT_APPLIED`, `READBACK_UNCONFIRMED`, `STATUS_UNRECOGNIZED`는 실패입니다.

## 테스트

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check mobileclaw_daily.py tests
```

테스트는 fake session을 사용하며 실제 혜택 서비스에 연결하지 않습니다.

## 개인정보

이 저장소는 자격 증명이나 개인정보를 저장하지 않습니다. 출력은 마스킹되며 생성된 보고서 파일은 Git에서 제외됩니다.

## 면책

합법적인 개인 자동화에 사용하세요. 혜택 규칙, 자격, 인터페이스, 잔액은 서비스 제공자가 관리합니다. 사용 책임은 사용자에게 있습니다.

---

[중국어 README로 돌아가기](../README.md) · [사용 규칙](../NOTICE.md) · [후원 및 Star History](../README.md#star-trail)
