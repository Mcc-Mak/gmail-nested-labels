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
- **除錯模式**：加上 `--no-archive` 旗標可跳過「移除 `\Inbox`（封存）」步驟，僅清除並標記，郵件留在收件匣以便檢驗。預設行為仍為封存。
- 這是 `main.py` 最重要的正確性檢查。

## 文件同步規則（硬性規定）

每次變更都必須同步更新 `doc/` 目錄下所有受影響的文件檔案——沒有「太小而不需更新」的文件變更。若變更引入新主題而 `doc/` 尚無對應檔案，則新增之並更新 `TOCTREE.md`（位於根目錄）。`README.md` 必須包含指向 `TOCTREE.md` 的參照。應涵蓋的文件類型包括但不限於：

- **目錄與索引**：`TOCTREE.md`（根目錄）、Glossary（詞彙表）
- **需求與規格**：Project Charter（專案章程）、PRD（產品需求文件）、SRS（軟體需求規格）、User Stories（使用者故事）、Project Goals (G) & Success Criteria (SC)（專案目標與成功準則）
- **架構與設計**：Architecture（架構文件）、ADR（架構決策記錄）、API 文件、Schema（資料結構）、ER（實體關係圖）
- **追溯與管理**：RTM（需求追溯矩陣，Requirements Traceability Matrix）、CRM（交叉參照矩陣，Cross-Reference Matrix）
- **測試與部署**：Test Plan（測試計畫）、Quick Start（快速入門）、Deployment Guide（部署指南）

## Mermaid 圖表規則

文件中應善用 Mermaid 圖表來視覺化流程與架構，尤其以下類型：

- **SequenceDiagram（時序圖）**：用於 IMAP 互動流程（連線 -> 擷取 -> 清除 -> 標記 -> 封存 -> 驗證）、`opencode run` 子程序呼叫等跨元件協作場景。
- **FlowChart（流程圖）**：用於決策邏輯（如網域擷取失敗時留在收件匣、`--no-archive` 分支）、標記工作流程等。
- 其他 Mermaid 支援的圖類（如 `ERDiagram`、`ClassDiagram`、`StateDiagram`）亦應在對應文件中適當使用。

圖表必須與程式碼保持同步：若流程變更，對應的 Mermaid 圖表必須一併更新。

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
