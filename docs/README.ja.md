<div align="center">

# 🦞 MobileClaw Daily

**MobileClaw 毎日 Token 特典 · 複数アカウント · status → claim → status / credits 再確認**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

</div>

> [!IMPORTANT]
> 本プロジェクトは無料です。転売、有料パッケージ化、有料代行、集客目的の転載、作者の偽装、著作権表示の削除を禁止します。詳細は [NOTICE.md](../NOTICE.md) を参照してください。

## 機能

MobileClaw Daily は L0NE-6 がオリジナルで保守する独立した単一ファイルスクリプトです。アクティビティ `1003` を確認し、受取可能なら claim を実行し、サーバー側の status と credits で結果を再確認します。

| 項目 | 内容 |
| :--- | :--- |
| 入力 | `MOBILECLAW_TOKENS` または `MOBILECLAW_TOKEN` |
| 出力 | アカウント別 JSON と最後の集計 JSON |
| 実行環境 | Python 3.9+、`requests` のみ |
| 配備 | Windows、Linux、Qinglong、GitHub Actions |
| 成功 | 最終状態または claim 受領証拠が確認され、credits を読み取れる |

## プロトコル

```text
POST status {"activityCodes":["1003"]}
  ├─ claimed   -> GET credits -> ALREADY_CLAIMED
  └─ claimable -> POST claim {"activityCode":"1003"}
                    -> POST status again
                    -> GET credits
                    -> CLAIMED / CLAIM_NOT_APPLIED / READBACK_UNCONFIRMED
```

HTTP 200 だけでは成功ではありません。信頼できる後状態または claim 受領証拠と、credits の読み取りが必要です。

## 認証情報

`MOBILECLAW_TOKENS` はカンマまたは改行区切りです。

```text
Bearer <token>
Authorization: <token>
Cookie: <name>=<value>; <name>=<value>
<token>
```

`=` を含まない値は Bearer Token、含む値は Cookie として扱います。`MOBILECLAW_TOKEN` は `MOBILECLAW_TOKENS` が空の場合だけ使用します。

実際の Token、Cookie、電話番号、認証ファイル、実行レポートをコミットしないでください。

## 資格エラー

| コード | 意味 |
| :--- | :--- |
| `C404003` | 未登録 |
| `C403001` | 実名認証が未完了 |
| `C401003` | 実名認証を審査中 |

これらは `INELIGIBLE` として報告されます。必要なアカウント手続きを完了してください。

## ローカル実行

```bash
python -m pip install -r requirements.txt
export MOBILECLAW_TOKEN='<Token または Cookie>'
python mobileclaw_daily.py
```

状態確認のみ：

```bash
python mobileclaw_daily.py --status
```

## Qinglong

1. `requests` をインストールします。
2. `mobileclaw_daily.py` をアップロードします。
3. `MOBILECLAW_TOKENS` または `MOBILECLAW_TOKEN` を設定します。
4. スケジュールタスクのコマンドを `task mobileclaw_daily.py` にします。
5. アカウントのルールに合わせて 1 日 1 回実行します。

## GitHub Actions

`main` への push ではテストを実行します。毎日のスケジュールではテスト後に受取を実行し、JSON レポート artifact をアップロードします。
認証情報 Secret が未設定の場合、定時受取は明示的な SKIPPED notice を出して正常終了します。認証情報を設定した後は、スクリプトの異常終了を失敗として扱います。

| Secret | 必須 | 値 |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | どちらか | 複数アカウントの Token/Cookie |
| `MOBILECLAW_TOKEN` | どちらか | 単一アカウントの Token/Cookie |

スケジュールは UTC `17 23 * * *`、北京時間 07:17 です。GitHub のスケジュールは遅延する場合があります。

## 成功条件

- `ALREADY_CLAIMED`: status が `claimed` で credits を読み取れる。
- `CLAIMED`: 最終 status が `claimed`、または claim 受領証拠が `claimed` で状態遅延を記録し、credits を読み取れる。
- `AVAILABLE`: 状態確認モードで `claimable` を確認し credits を読み取れる。
- `CLAIM_NOT_APPLIED`、`READBACK_UNCONFIRMED`、`STATUS_UNRECOGNIZED` は失敗です。

## テスト

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check mobileclaw_daily.py tests
```

テストは fake session を使用し、実際の受取サービスへ接続しません。

## プライバシー

本リポジトリは認証情報や個人情報を保存しません。出力は秘匿化され、生成レポートは Git の対象外です。

## 免責事項

合法的な個人自動化のために使用してください。特典ルール、資格、インターフェース、残高はサービス提供者が管理します。利用は自己責任です。

---

[中国語 README に戻る](../README.md) · [利用規則](../NOTICE.md) · [投げ銭と Star History](../README.md#star-trail)
