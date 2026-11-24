<div align="center">

# 🦞 MobileClaw Daily

**MobileClaw 每日 Token 福利 · 多帳號領取 · status → claim → status / credits 回讀**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

> [!IMPORTANT]
> 本專案永久免費。禁止倒賣、付費包裝、代部署收費、搬運引流、冒充作者或刪除版權資訊。完整規則見 [NOTICE.md](../NOTICE.md)。

## 功能

MobileClaw Daily 是 L0NE-6 原創維護的獨立單檔腳本。它會檢查活動 `1003`，可領取時執行 claim，並透過伺服器端 status 與 credits 回讀確認結果。

| 項目 | 說明 |
| :--- | :--- |
| 輸入 | `MOBILECLAW_TOKENS` 或 `MOBILECLAW_TOKEN` |
| 輸出 | 每帳號 JSON 與最後一筆彙總 JSON |
| 執行環境 | Python 3.9+，僅需 `requests` |
| 部署 | Windows、Linux、青龍、GitHub Actions |
| 成功 | 最終狀態或 claim 回執已確認，且 credits 可讀取 |

## 協議流程

```text
POST status {"activityCodes":["1003"]}
  ├─ claimed   -> GET credits -> ALREADY_CLAIMED
  └─ claimable -> POST claim {"activityCode":"1003"}
                    -> POST status again
                    -> GET credits
                    -> CLAIMED / CLAIM_NOT_APPLIED / READBACK_UNCONFIRMED
```

只有 HTTP 200 不算成功。成功結果必須有可信後態或 claim 回執，並成功讀取 credits。

## 憑據格式

`MOBILECLAW_TOKENS` 支援逗號或換行分隔：

```text
Bearer <token>
Authorization: <token>
Cookie: <name>=<value>; <name>=<value>
<token>
```

不含 `=` 的值按 Bearer Token 處理；含 `=` 的值按 Cookie 處理。`MOBILECLAW_TOKEN` 僅在 `MOBILECLAW_TOKENS` 為空時使用。

請勿提交真實 Token、Cookie、手機號、認證檔案或執行報告。

## 資格錯誤

| 代碼 | 含義 |
| :--- | :--- |
| `C404003` | 尚未註冊 |
| `C403001` | 尚未完成實名認證 |
| `C401003` | 實名認證審核中 |

上述情況會標記為 `INELIGIBLE`，請先完成帳號所需操作。

## 本機執行

```bash
python -m pip install -r requirements.txt
export MOBILECLAW_TOKEN='<你的 Token 或 Cookie>'
python mobileclaw_daily.py
```

只查狀態：

```bash
python mobileclaw_daily.py --status
```

## 青龍

1. 安裝 `requests`。
2. 上傳 `mobileclaw_daily.py`。
3. 新增 `MOBILECLAW_TOKENS` 或 `MOBILECLAW_TOKEN`。
4. 建立排程，命令填 `task mobileclaw_daily.py`。
5. 依帳號規則每天執行一次。

## GitHub Actions

工作流在 `main` 分支 push 時執行測試；每日排程會先測試，再領取並上傳 JSON 報告 artifact。
未設定憑據 Secret 時，定時領取會輸出明確 SKIPPED notice 並成功結束；設定憑據後，腳本異常仍會保持失敗狀態。

| Secret | 必填 | 值 |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | 二選一 | 多帳號 Token 或 Cookie |
| `MOBILECLAW_TOKEN` | 二選一 | 單帳號 Token 或 Cookie |

排程為 UTC `17 23 * * *`，即北京時間 07:17。GitHub 排程可能延遲。

## 成功判據

- `ALREADY_CLAIMED`：status 回讀為 `claimed`，且 credits 可讀。
- `CLAIMED`：最終 status 為 `claimed`，或 claim 回執為 `claimed` 且已記錄狀態延遲，同時 credits 可讀。
- `AVAILABLE`：查詢模式確認可領取並讀取 credits。
- `CLAIM_NOT_APPLIED`、`READBACK_UNCONFIRMED`、`STATUS_UNRECOGNIZED` 均為失敗。

## 測試

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check mobileclaw_daily.py tests
```

測試使用 fake session，不連線真實領取服務。

## 隱私

本倉庫不保存憑據或個人資料。輸出會脫敏，產生的報告檔案已被 Git 忽略。

## 免責聲明

本專案供合法的個人自動化使用。活動規則、資格、介面與餘額由服務方決定，使用風險自負。

---

[返回簡體中文 README](../README.md) · [使用規則](../NOTICE.md) · [投喂與星軌](../README.md#star-trail)
