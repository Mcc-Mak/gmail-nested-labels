# AGENTS.md

本專案為全新專案。**`SPEC.md` 是所有專案邏輯的權威來源**——任何變更前請先閱讀它。以下內容重複或 sharpen 規範中容易出錯的部分。

## 分支與 CI 流程

- 開發僅在 `dev-001` 進行。不得直接提交到 `dev` 或 `main`。
- 自動合併為無閘門且單向：`dev-001` -> `dev` -> `main`，透過 `.github/workflows/auto-merge.yml`。
- 開發變更週期由 `commit.sh`（或 `Makefile`）標準化：提示更新 `CHANGELOG.md` 的語意化版本項目 -> 暫存 -> 提交 -> 推送到 `dev-001`。不得繞過它。
- 提交訊息格式嚴格：`[{X.X.X}] {message}` 並附詳細內文。版本為語意化 `major.minor.patch`。

## 核心標籤規則（不得近似）

- 取寄件者網域，以 `.` 切分，反轉各部分，以 `-` 接合成單一扁平 Gmail 標籤。
- 標準範例：`hko.gov.hk` -> 標籤 `hk-gov-hko`。在以 `X-GM-LABELS` 指派前，先以 IMAP `CREATE` 建立該標籤。切勿使用 `/`：它會觸發 Gmail 自動建立空的父標籤。
- 每封郵件的工作流程為 **清除 -> 標記 -> 封存**：先移除 `\Inbox` 以外的所有現有標籤，再套用扁平網域標籤，然後（若有套用標籤）移除 `\Inbox` 以封存。無法擷取網域的郵件留在收件匣不標記。
- **除錯模式**：加上 `--no-archive` 旗標可跳過「移除 `\Inbox`（封存）」步驟，僅清除並標記，郵件留在收件匣以便檢檢驗。預設行為仍為封存。
- 這是 `main.py` 最重要的正確性檢查。

## 文件同步規則（硬性規定）

每次變更都必須同步更新 doc/*.md——包括 TOCTREE（TOCTREE.md 位於根目錄）、Project Charter、PRD、SRS、ADR、API、Schema、ER、Quick Start 等所有受影響的文件檔案。若變更引入新主題而 doc/ 尚無對應檔案，則新增之並更新 TOCTREE.md。沒有「太小而不需更新」的文件變更。

## 本地化規則

本專案所有文件與使用者面向文字（`.md` 文件、程式碼註解/docstring、`print` 輸出、CLI 說明、shell 提示、CI 步驟名稱）一律使用**繁體中文**。以下保持原文不譯：協定字面值（如 `\Inbox`、`INBOX`、`X-GM-LABELS`、`RFC822`）、環境變數名、檔名、分支名、套件名、識別碼，以及 `LICENSE`（法律授權文本為標準 MIT 英文原文，不翻譯）。

## 安全（硬性規定）

- 絕不提交 `.env`、`credentials.json`、`token.json` 或 `venv/`。`.gitignore` 必須排除它們全部。
- Gmail 存取使用 IMAP + 應用程式密碼（存於 `.env` 的 `GMAIL_USER` / `GMAIL_APP_PASSWORD`）。不使用 OAuth2 的 `credentials.json` 或 `token.json`，但為安全起見仍將它們 git-ignore。
- 不需 AI API 金鑰——主題分析使用 OpenCode 內建模型（`big-pickle`），透過 `opencode run` 呼叫。

## 技術棧與交付物

- Python，以 `venv` 隔離。相依套件釘選於 `requirements.txt`。
- Gmail 存取：**IMAP**（`imapclient`）搭配 Gmail 應用程式密碼——免 Google Cloud Console。
- AI 主題分析：**OpenCode 內建模型**（`opencode/big-pickle`）透過 `opencode run` 子程序——免 API 金鑰、免信用卡。
- 進入點為 `main.py`（Workflow-1）：IMAP 連線 -> 擷取 N 封最新收件匣郵件 -> 清除 \Inbox 以外所有標籤 -> 透過 `CREATE` + `X-GM-LABELS` 套用扁平網域標籤 -> 封存（移除 `\Inbox`，可用 `--no-archive` 停用） -> OpenCode 主題分析寫入 `themes-ai.json`。
- AI 主題輸出檔名固定為 `themes-ai.json`。
