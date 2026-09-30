# Gmail 自動化：扁平網域標記 + AI 主題分析

Workflow-1（見 `SPEC.md`）：以 IMAP 連線 Gmail，擷取最新 N 封收件匣郵
件，依反轉寄件者網域指派扁平標籤，再以 OpenCode 內建模型將郵件依主題
分組，結果寫入 `themes-ai.json`。

## 前置需求

- Python 3.9+
- 已啟用**兩步驟驗證**的 Gmail 帳號
- 已安裝 **OpenCode** CLI（用於主題分析——免 API 金鑰）

> **免 Google Cloud Console、免信用卡、免 API 金鑰。** Gmail 存取使用
> IMAP + 應用程式密碼；AI 分析使用 OpenCode 內建免費模型
>（`big-pickle`）。

## 安裝

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Gmail 應用程式密碼

1. 在 Google 帳號啟用**兩步驟驗證**：
   https://myaccount.google.com/security
2. 產生**應用程式密碼**：
   https://myaccount.google.com/apppasswords
   （應用選「Mail」，裝置名稱任意。）
3. 複製 16 字元密碼。

## 設定環境

```bash
cp .env.example .env
```

編輯 `.env`：

```
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

> `.env` 已被 git-ignore，絕不可提交。

## 用法

```bash
source venv/bin/activate
python main.py               # 使用 .env 中的 EMAIL_COUNT（預設 10）
python main.py -n 25         # 處理最新 25 封收件匣郵件
python main.py --model opencode/big-pickle
python main.py --no-archive  # 除錯模式：僅清除並標記，不封存（郵件留在收件匣）
```

輸出：`themes-ai.json`。

### 標記規則

對每封最新收件匣郵件，腳本會：移除 `Inbox` 以外的所有現有標籤（乾淨
狀態）；建立（若不存在）並指派單一扁平 Gmail 標籤（由反轉寄件者網域
而來）；然後，若已套用標籤，移除 `Inbox` 標籤以封存郵件。

寄件者網域以 `.` 切分、反轉，以 `-` 接合成單一扁平 Gmail 標籤。範例：
`hko.gov.hk` -> `hk-gov-hko`。標籤若不存在則以 IMAP `CREATE` +
`X-GM-LABELS` 建立。不使用 `/`，故 Gmail 不會自動建立空的父標籤。無法
擷取網域的郵件留在收件匣不標記。

### 除錯模式

加上 `--no-archive` 旗標可跳過封存步驟（不移除 `\Inbox`），僅清除並
標記，郵件留在收件匣以便檢驗標籤是否正確套用。預設行為為封存。

## 開發工作流程

所有開發在 `dev-001` 進行。使用標準化變更週期腳本：

```bash
./commit.sh
```

它會提示輸入 `CHANGELOG.md` 的語意化版本項目，暫存所有變更，以
`[{X.X.X}] {message}` 格式提交（附詳細內文），並推送到 `dev-001`。該
推送觸發無閘門自動合併 `dev-001 -> dev -> main`，由
`.github/workflows/auto-merge.yml` 執行。
