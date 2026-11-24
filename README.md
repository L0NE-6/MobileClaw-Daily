<div align="center">

<sub><strong>L0NE-6 · MOBILECLAW SIGNAL</strong></sub>

# 🦞 MobileClaw Daily

**MobileClaw 每日 Token 福利 · 多账号领取 · status → claim → status / credits 回读**

> 当前版本：**v1.0.1**（2026-11-24） · 独立仓库维护版 · 单文件自包含 · 不以内网或 HTTP 200 冒充成功

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

🔁 多账号隔离 · 🧾 JSON 报告 · ✅ 服务端回读 · 🛡️ 凭据脱敏 · 🐧 青龙友好 · ☁️ GitHub Actions · 🧪 单元测试

<img src="https://img.shields.io/github/v/release/L0NE-6/MobileClaw-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" />
<img src="https://img.shields.io/github/stars/L0NE-6/MobileClaw-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" />
<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20%E9%9D%92%E9%BE%99-4EAA25?style=for-the-badge&logo=linux&logoColor=white" />
<img src="https://img.shields.io/badge/Deploy-%E9%9D%92%E9%BE%99%20%7C%20GitHub%20Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />
<a href="https://github.com/L0NE-6/MobileClaw-Daily/releases"><img src="https://img.shields.io/badge/%E2%AC%87%20Download-Releases-2ea44f?style=for-the-badge&logo=github" /></a>

[✨ 30 秒速览](#quick-overview) · [🔐 凭据格式](#credentials) · [🚀 青龙部署](#qinglong) · [☁️ GitHub Actions](#actions) · [⌨️ 命令行](#cli) · [✅ 成功判据](#success) · [🧠 设计原则](#design) · [📁 目录结构](#directory) · [🚫 使用边界](#usage-policy) · [✦ 星轨](#star-trail)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> **官方版本永久免费。禁止倒卖。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与收款码制造官方授权假象。

本仓库、脚本、部署说明和 Release 下载始终免费公开。禁止把本项目包装为付费资源、内部版、独家版、会员权益、收费课程、代部署服务或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商和付费平台进行涨粉、截流、倒卖或引流；禁止删除作者与版权信息后冒充原创。

官方仓库和 Release 始终免费。第三方以“下载费、激活费、内部版、代部署、会员门槛”等名义收费，均与作者无关。完整规则见 **[NOTICE.md](NOTICE.md)**。

---

<a id="quick-overview"></a>
## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 自动检查 MobileClaw 每日 Token 福利，按需领取，并在领取后回读活动状态和 Token 余额。 |
| **输入** | `MOBILECLAW_TOKENS` 多账号 Token/Cookie，或 `MOBILECLAW_TOKEN` 单账号凭据。 |
| **输出** | 每账号一条 JSON、最后一条汇总 JSON、领取状态、前后状态、Token 余额和失败分类。 |
| **部署** | Windows、Linux、青龙面板、GitHub Actions。 |
| **依赖** | Python 3.9+；运行时仅依赖 `requests`。 |
| **成功判据** | `status → claim → status / credits` 至少形成可信后态；单独 HTTP 200 不算成功。 |

## ✨ 这是什么

MobileClaw Daily 是 L0NE-6 原创维护的独立单文件签到脚本。它只做一件事：**检查活动 1003 的每日 Token 福利，能领就领，领完再回读**。

脚本不依赖额外调度模块，青龙只需上传一个 Python 文件。

核心行为：

- 多账号逐个执行，每个账号使用独立 Session；
- Bearer Token 与 Cookie 两种凭据都支持；
- 先查状态，已领取则只回读余额；
- 可领取时发起 claim，再查状态并读取 credits；
- 遇到注册、实名认证或审核中时归类为 `INELIGIBLE`；
- 日志和 JSON 对 Token、Cookie、异常回包中的敏感值做脱敏；
- 任意账号失败不阻断后续账号。

---

## 🔁 协议与回读流程

脚本固定使用活动码 `1003`，完整链路如下：

```text
POST /desktop/manager/token-welfare/status
  body: {"activityCodes":["1003"]}
        |
        +-- claimed   -> GET /credits/v2/exp-credit -> ALREADY_CLAIMED
        |
        +-- claimable -> POST /desktop/manager/token-welfare/claim
        |                  body: {"activityCode":"1003"}
        |                  |
        |                  +-> POST status again
        |                  +-> GET credits
        |                  +-> 判定 CLAIMED / CLAIM_NOT_APPLIED / READBACK_UNCONFIRMED
        |
        +-- unknown   -> STATUS_UNRECOGNIZED
```

### 状态判定

脚本兼容常见的 `claimed`、`isClaimed`、`claimable`、`canClaim`、`claimStatus`、`status` 等字段和少量文本状态。解析结果只有三类：

| 内部状态 | 含义 |
| :--- | :--- |
| `claimed` | 服务端明确表示今天已领取 |
| `claimable` | 服务端明确表示可以领取 |
| `unknown` | 回包存在但无法确认状态，脚本不会猜测成功 |

### 回读规则

- 已领取：必须再次读到 `claimed`，再读取 credits；
- 新领取：claim 后重新读取 status，再读取 credits；
- claim 回执明确显示已领取，但最终 status 暂时滞后：保留回执证据，结果仍标为 `CLAIMED`，并在 message 中写明“claim receipt confirmed”；
- claim 成功但最终 status 仍为 `claimable`：判为 `CLAIM_NOT_APPLIED`；
- status 无法识别：判为 `READBACK_UNCONFIRMED`；
- credits 无法解析：判为 `CREDITS_UNRECOGNIZED`。

---

<a id="credentials"></a>
## 🔐 凭据格式

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | ✅ 二选一 | 多账号凭据，逗号或换行分隔。脚本优先读取此变量。 |
| `MOBILECLAW_TOKEN` | ✅ 二选一 | 单账号凭据；仅当 `MOBILECLAW_TOKENS` 为空时使用。 |
| `MOBILECLAW_BASE_URL` | ⬜ | 可选基址覆盖，仅用于自建测试或接口迁移；默认使用脚本内置基址。 |

### `MOBILECLAW_TOKENS` 支持的写法

```text
Bearer <token>
Authorization: <token>
Cookie: <cookie>
<token>
<name>=<value>; <name>=<value>
```

判定规则：

- 以 `Bearer ` 开头：Bearer Token；
- 以 `Authorization:` 开头：Bearer Token；
- 以 `Cookie:` 开头：Cookie；
- 不含 `=`：按 Bearer Token 处理；
- 含 `=`：按 Cookie 处理。

多账号示例：

```text
Bearer <账号一的 Token>
Cookie: <账号二的 Cookie>
Authorization: <账号三的 Token>
```

> 凭据只通过环境变量或 GitHub Secrets 注入。不要把真实 Token、Cookie、手机号或认证文件写进仓库。

### 凭据从哪来

使用你自己的 MobileClaw 登录会话，从已登录的客户端或网页请求中提取当前 `Authorization: Bearer ...`，或完整 Cookie。不同客户端版本的存储方式可能变化；本项目不内置凭据提取器，也不读取本机认证目录。

---

## 🚧 实名、注册与资格错误

以下业务码会直接归类为 `INELIGIBLE`，不做无意义重试：

| 业务码 | 脚本结论 | 需要完成的动作 |
| :--- | :--- | :--- |
| `C404003` | 当前用户未注册 | 先在移动云完成注册 |
| `C403001` | 当前用户未完成实名认证 | 先完成实名认证 |
| `C401003` | 实名认证审核中 | 等待审核通过后再运行 |

资格问题属于账号状态问题，不是 Token 格式问题。脚本会保留脱敏后的服务端 message，方便判断下一步。

---

<a id="quickstart"></a>
## 🚀 本地快速开始

```powershell
python -m pip install -r requirements.txt

$env:MOBILECLAW_TOKEN = "<你的 Bearer Token 或 Cookie>"
python mobileclaw_daily.py
```

多账号：

```powershell
$env:MOBILECLAW_TOKENS = @"
Bearer <账号一 Token>
Cookie: <账号二 Cookie>
"@
python mobileclaw_daily.py
```

只查状态、不执行 claim：

```powershell
python mobileclaw_daily.py --status
```

Linux / macOS：

```bash
python -m pip install -r requirements.txt
export MOBILECLAW_TOKEN='<你的 Bearer Token 或 Cookie>'
python mobileclaw_daily.py
```

---

<a id="qinglong"></a>
## 🐧 青龙面板部署

| 步骤 | 操作 |
| :---: | :--- |
| **1** | 安装依赖：`pip3 install requests` |
| **2** | 上传 `mobileclaw_daily.py` 到青龙脚本目录 |
| **3** | 在环境变量中新增 `MOBILECLAW_TOKENS` 或 `MOBILECLAW_TOKEN` |
| **4** | 新建定时任务，命令填 `task mobileclaw_daily.py` |
| **5** | 建议每天运行一次，例如 `17 7 * * *`，具体时间按账号规则调整 |

> 青龙任务优先使用 `task mobileclaw_daily.py`，确保面板环境变量被注入。不要用未经过青龙运行器的裸 Python 命令排查“变量明明存在却读不到”的问题。

多账号在青龙变量中直接换行或逗号分隔即可。不要把多个账号拼成一个带引号的 JSON 字符串。

---

<a id="actions"></a>
## ☁️ GitHub Actions 部署

本仓库内置 [`.github/workflows/mobileclaw.yml`](.github/workflows/mobileclaw.yml)。

### 触发规则

| 事件 | 行为 |
| :--- | :--- |
| `push` 到 `main` | 只运行 unittest、compileall 和 ruff 检查 |
| `schedule` | 每天一次：先跑测试，再执行领取并上传报告 artifact |
| `workflow_dispatch` | 手动执行同一套测试与领取流程 |

未配置 `MOBILECLAW_TOKENS` / `MOBILECLAW_TOKEN` 时，定时领取会输出明确 SKIPPED notice 并成功结束；配置凭据后，脚本异常仍会保持失败状态。

### Secrets

进入 **Settings → Secrets and variables → Actions**，按需添加：

| Secret | 必填 | 值 |
| :--- | :---: | :--- |
| `MOBILECLAW_TOKENS` | ✅ 二选一 | 多账号 Token/Cookie，换行或逗号分隔 |
| `MOBILECLAW_TOKEN` | ✅ 二选一 | 单账号 Token/Cookie |

工作流只把上述两个 Secret 映射为同名环境变量。不会把凭据写进仓库，也不会提交运行状态。

### 内置定时

| 北京时间 | UTC cron | 说明 |
| :---: | :---: | :--- |
| 07:17 | `17 23 * * *` | 每日一次，避开整点高峰 |

> GitHub `schedule` 使用 UTC。GitHub 的定时任务属于 best-effort，可能延迟或被跳过；需要精确时间时使用手动触发或外部调度。

### 报告 artifact

每次领取任务都会上传：

- `mobileclaw-report.json`：完整 JSON 数组；
- `mobileclaw-report.jsonl`：脚本原始逐行 JSON，最后一行是汇总。

即使账号领取失败，只要工作流进入领取步骤，`if: always()` 仍会尝试上传报告。

---

<a id="cli"></a>
## ⌨️ 命令行与输出

```bash
python mobileclaw_daily.py            # 检查并领取
python mobileclaw_daily.py --status   # 只查状态与 credits
python mobileclaw_daily.py status     # 兼容位置参数写法
```

退出码：

| 退出码 | 含义 |
| :---: | :--- |
| `0` | 所有账号均为可信成功 |
| `1` | 至少一个账号失败或回读未确认 |
| `2` | 未配置凭据或配置格式错误 |

输出是 JSON Lines：每个账号一行，最后一行是汇总。汇总字段包括：

```json
{
  "provider": "mobileclaw",
  "accounts": 2,
  "success": 2,
  "failed": 0,
  "results": []
}
```

单账号结果字段：

| 字段 | 说明 |
| :--- | :--- |
| `account` | 自动生成的账号序号，不含原始凭据 |
| `result` | 分类结果，如 `CLAIMED`、`ALREADY_CLAIMED` |
| `ok` | 是否达到可信成功条件 |
| `before_state` | 领取前状态 |
| `after_state` | 回读后的状态 |
| `claimed` | 是否确认已领取 |
| `credits` | 回读到的 Token 余额 |
| `http_status` | 最后一次关键请求的 HTTP 状态 |
| `message` | 脱敏后的结果说明 |

---

## 🧭 结果码

| 结果码 | 是否成功 | 含义 |
| :--- | :---: | :--- |
| `CLAIMED` | ✅ | 新领取已确认，credits 已读取 |
| `ALREADY_CLAIMED` | ✅ | 运行前已领取，回读确认 |
| `AVAILABLE` | ✅ | 查询模式发现可领取，未执行 claim |
| `INELIGIBLE` | ❌ | 未注册、未实名或审核中 |
| `AUTH_EXPIRED` | ❌ | Token/Cookie 无效或过期 |
| `RATE_LIMITED` | ❌ | HTTP 429 |
| `CLAIM_NOT_APPLIED` | ❌ | claim 返回成功，但状态仍可领取 |
| `READBACK_UNCONFIRMED` | ❌ | 回读状态无法确认 |
| `STATUS_UNRECOGNIZED` | ❌ | 初始状态无法识别 |
| `CREDITS_UNRECOGNIZED` | ❌ | credits 回包没有可解析余额 |
| `BUSINESS_ERROR` | ❌ | 服务端业务错误 |
| `HTTP_ERROR` | ❌ | 非 2xx HTTP 错误 |
| `REDIRECT` | ❌ | 请求被重定向，脚本不跟随 |
| `NETWORK_ERROR` | ❌ | 网络异常 |
| `INVALID_JSON` | ❌ | 回包不是 JSON |
| `CONFIG_ERROR` | ❌ | 环境变量或基址配置错误 |

---

<a id="success"></a>
## ✅ 成功判据

本项目不把“脚本跑了”“HTTP 200”“claim 接口返回 success”单独当成成功。

| 场景 | 必须满足 |
| :--- | :--- |
| 今日已领取 | status 回读为 `claimed`，credits 读取成功 |
| 今日新领取 | claim 后 status 回读为 `claimed`，credits 读取成功 |
| claim 回执明确已领取但状态滞后 | claim 回执状态为 `claimed`，最终 status 已记录，credits 读取成功 |
| 只查状态 | status 为 `claimed` 或 `claimable`，credits 读取成功 |

若最终 status 仍为 `claimable`，结果是 `CLAIM_NOT_APPLIED`，不是成功。若无法识别状态，结果是 `READBACK_UNCONFIRMED`，也不是成功。

---

## 🧪 测试与静态检查

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check mobileclaw_daily.py tests
```

测试全部使用 fake response / fake session：

- 不读取真实账号；
- 不访问真实领取接口；
- 覆盖新领取、已领取、回执滞后、HTTP 错误、多账号隔离、凭据脱敏、实名错误、汇总输出和配置错误。

> 单测通过只证明代码路径正确，不代表某个真实账号今天已领取成功。真实结果必须由实际运行后的 status 和 credits 回读证明。

---

## 🧠 设计原则

- **协议先行**：先固定活动码、请求体、状态字段和回读字段，再实现流程；
- **服务端回读**：每个成功结论都尽量绑定 status、claim 回执或 credits；
- **账号隔离**：一个账号失败，不影响后续账号；
- **幂等优先**：已领取识别为中性成功，不重复请求 claim；
- **不掩盖失败**：状态不明、余额不明、claim 未落账都单独报告；
- **最小依赖**：运行时只有 `requests`；
- **敏感信息脱敏**：Token、Cookie 和异常回包中的凭据替换为 `[REDACTED]`；
- **固定证据**：协议字段和成功判据以可复核的请求与回包为准。

---

## 🔒 隐私说明

本仓库不包含任何账号、手机号、Token、Cookie、JWT、设备号、认证文件或运行日志。所有凭据均由环境变量、GitHub Secrets 或你自己的运行环境注入。

请勿提交：

- `*_tokens.json`
- `*_token.txt`
- `*_cookies.json`
- `auth.json`
- `login_result.json`
- `mobileclaw-report.json`
- `mobileclaw-report.jsonl`
- 包含真实手机号、设备号或 Token 的截图和日志

`.gitignore` 已覆盖常见运行产物，但提交前仍应人工检查。

---

## 📁 目录结构

```text
MobileClaw-Daily/
├── .github/
│   └── workflows/
│       └── mobileclaw.yml
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.zh-Hant.md
│   ├── README.ja.md
│   ├── README.ko.md
│   └── README.pt-BR.md
├── tests/
│   └── test_mobileclaw_daily.py
├── mobileclaw_daily.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 📦 版本与发布

- 当前版本：`v1.0.1`（2026-11-24）；
- 本仓库首版不创建远端、不创建 tag、不创建 Release；
- 后续每次实质更新单独发布版本，历史版本保留；
- 公开包不得包含凭据、手机号、Cookie、JWT、运行日志或本机路径。

下载页预留：<https://github.com/L0NE-6/MobileClaw-Daily/releases>

---

## ⚠️ 免责声明

本项目用于个人学习和合法的个人自动化。MobileClaw 的活动规则、接口、资格和余额口径由服务方决定；使用前请确认对应服务条款，并自行承担账号、网络、活动和接口变化带来的风险。

---

## ☕ 支持与投喂

脚本完全免费，无广告、无功能限制。如果它确实帮你省了时间，欢迎自愿赞赏；不影响任何功能，也不影响 Issue 响应。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>
<p align="center"><sub>💚 微信支付（左） &nbsp;|&nbsp; 💙 支付宝（右）</sub></p>

> 收款码仅用于向作者自愿赞赏。任何第三方以代下载、代部署、内部资源或会员群为由收费，均与作者无关。禁止倒卖本项目。

---

## 💬 反馈与贡献

- [提交 Issue](https://github.com/L0NE-6/MobileClaw-Daily/issues)
- [发起 Pull Request](https://github.com/L0NE-6/MobileClaw-Daily/pulls)

反馈问题时，请附公开规则、脱敏后的请求/响应字段、运行结果和复现步骤。不要上传真实 Token、Cookie、手机号、设备号或完整账号日志。

---

<a id="star-trail"></a>
## ✦ 星轨 Star Trail

> 每一次 Star 都是一枚信号灯。这里记录 MobileClaw Daily 与社区一起走过的轨迹，也提醒我继续把自动化做得更稳、更透明。

<a href="https://star-history.com/#L0NE-6/MobileClaw-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/MobileClaw-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/MobileClaw-Daily&type=Date" />
    <img alt="MobileClaw Daily Star Trail" src="https://api.star-history.com/svg?repos=L0NE-6/MobileClaw-Daily&type=Date" />
  </picture>
</a>

---

<div align="center">
  <sub>L0NE-6 · MOBILECLAW SIGNAL &nbsp;|&nbsp; 点个 <b>Star</b>，让下一轮领取有迹可循 ✨</sub>
</div>
