# Changelog

所有重要變更列於此處。版本遵循語意化版本（major.minor.patch）。

## [Unreleased]

## [0.3.7] - 2026-09-30
- 修復 SonarQube S3776（CRITICAL, MAINTAINABILITY）：`label_emails`
  認知複雜度 30（上限 15）。拆分為 6 個私有輔助函式
  （`_resolve_targets`、`_clear_labels`、`_apply_labels`、
  `_verify_labels`、`_archive_emails`、`_verify_and_report`），
  `label_emails` 本身降為單純協調器。同步更新 API 文件。

## [0.3.4] - 2026-09-30
- 修復封存靜默失敗：`remove_gmail_labels(uids, ["\\Inbox"])` 從 INBOX
  執行時為 no-op（Gmail 的 `X-GM-LABELS` 在 INBOX 中不回報 `\Inbox`），
  導致郵件從未真正封存，但驗證（`"\\Inbox" in labels`）因 `\Inbox` 不
  出現而永遠回 False，虛報「已封存」。
- 根因調查發現 Gmail IMAP 兩個關鍵行為：(1) `X-GM-LABELS` 不含
  `\Inbox`（INBOX 中不回報），(2) `STORE -FLAGS \Inbox` 被 Gmail 拒絕
  （`BAD Invalid Arguments`），(3) Gmail 各資料夾 UID 獨立（INBOX UID
  與 All Mail UID 指向不同郵件），無法跨資料夾操作。
- 封存方法改為 `STORE +FLAGS \Deleted` + `UID EXPUNGE`：從 INBOX
  移除郵件即等同 Gmail 封存，使用者標籤保留在「全部郵件」中。
  驗證改為封存前檢查標籤、封存後搜尋 INBOX 確認 UID 已移除。
- 新增 ADR-007（封存方法：STORE \Deleted + EXPUNGE），同步更新架構
  文件（Mermaid 時序圖與流程圖）、SRS、RTM、API 文件、測試計畫、PRD。

## [0.3.3] - 2026-09-30
- 修復 `ensure_label` 在 Gmail 帳號有舊 `/` 格式標籤時的衝突：Gmail
  將 `-` 和 `/` 視為等價，導致 `CREATE "com-github"` 在 `"com/github"`
  已存在時傳回 `ALREADYEXISTS`，且 `add_gmail_labels` 套用舊 `/` 格式
  標籤，驗證失敗。現在 `ensure_label` 在偵測到此衝突時，刪除舊 `/`
  格式標籤後重試建立 `-` 格式標籤。
- 新增 ADR-006（舊 `/` 格式標籤衝突處理）、SR-10、TC-06，並同步更新
  API 文件、架構文件（Mermaid 時序圖與流程圖）、PRD、RTM。

## [0.3.2] - 2026-09-30
- 建立 `doc/` 目錄與 16 份文件檔案：Glossary、Project Charter、PRD、
  SRS、User Stories、Project Goals (G) & Success Criteria (SC)、
  Architecture、ADR、API、Schema、ER、RTM、CRM、Test Plan、Quick Start、
  Deployment Guide。
- 建立根目錄 `TOCTREE.md` 作為文件索引。
- `README.md` 新增指向 `TOCTREE.md` 的參照。
- `AGENTS.md` 文件同步規則新增：`README.md` 必須包含指向
  `TOCTREE.md` 的參照。
- 文件中使用 Mermaid 圖表：SequenceDiagram（IMAP 互動時序）、
  FlowChart（標記工作流程、CI/CD 流程）、StateDiagram（郵件狀態轉移）、
  ERDiagram（實體關係圖）。

## [0.3.1] - 2026-09-30
- 擴充 AGENTS.md 文件同步規則：涵蓋 Architecture、RTM、CRM、User
  Stories、Project Goals (G) & Success Criteria (SC) 等文件類型。
- 新增「Mermaid 圖表規則」一節：SequenceDiagram 用於 IMAP 互動流程、
  FlowChart 用於決策邏輯，圖表須與程式碼保持同步。
- 修正 typo：檢檢驗 -> 檢驗。

## [0.3.0] - 2026-09-30
- 全專案本地化為繁體中文：`.md` 文件、程式碼 docstring/註解、`print`
  輸出、CLI 說明、`commit.sh` 提示、CI 步驟名稱。協定字面值（如
  `\Inbox`、`INBOX`、`X-GM-LABELS`、`RFC822`）、環境變數名、檔名、
  分支名、套件名保持原文。`LICENSE` 維持標準 MIT 英文原文。
- 新增 `--no-archive` 除錯旗標：跳過「移除 `\Inbox`（封存）」步驟，
  僅清除並標記，郵件留在收件匣以便檢驗標籤是否正確套用。預設行為仍
  為封存。驗證邏輯隨之調整：除錯模式下成功 = 標籤已套用（忽略
  `\Inbox` 是否存在）。
- AGENTS.md 新增「文件同步規則」（硬性規定）與「本地化規則」兩節。

## [0.2.3] - 2026-09-30
- 修復核心標記 bug：`label_emails` 回報「labeled ... and archived」但
  實際上什麼也沒發生（郵件留在收件匣、標籤未建立）。根因為靜默 no-op：
  `UID STORE` 在指令未生效時為 no-op，且 `ensure_label` 吞掉所有
  `create_folder` 錯誤（`except Exception: pass`），以致失敗被隱藏。
  逐 UID 迴圈（100 封郵件約 300 次往返）也可能觸發 Gmail IMAP 速率
  限制。
- 重寫 `label_emails`：以標籤為單位批次處理（每組一次 CREATE + 一次
  add-labels + 一次 remove-\Inbox），一次呼叫擷取所有現有標籤，並
  **驗證**結果（重新擷取 `X-GM-LABELS`）——郵件僅在 `\Inbox` 確實
  不存在時才算封存。失敗現以逐 UID 回報，不再虛報成功。
- `ensure_label` 不再吞掉錯誤：僅容忍 `ALREADYEXISTS`，其他錯誤重新
  拋出，使真正的建立失敗可見。

## [0.2.2] - 2026-09-30
- 強化 `auto-merge.yml` 以應對間歇性 `git push origin main` 失敗
  （0.1.0 與 0.2.0 執行時出現 HTTP 403 RPC 錯誤；0.2.1 成功，確認
  失敗為暫時性）。
- 新增 `concurrency` 控制（`cancel-in-progress: true`），使快速連續
  推送到 `dev-001` 不再讓兩個 `merge-to-main` 工作競爭同一 `main`
  ref。
- 在兩個推送步驟加入 3 次重試迴圈（重新擷取 + 重新合併 + 重試）以
  渡過暫時性 RPC 失敗。

## [0.2.1] - 2026-09-30
- 修復 `label_emails`（清除步驟）崩潰：`get_gmail_labels` 回傳 dict
  `{uid: (labels,)}`，但程式碼迭代 dict 本身，將整數 UID 當作標籤
  傳入 `remove_gmail_labels` -> `AttributeError`。現正確取出該 UID
  的標籤元組。

## [0.2.0] - 2026-09-30
- 工作流程改為清除 -> 標記 -> 封存：對每封擷取的郵件，移除 `\Inbox`
  以外的所有現有標籤，套用扁平網域標籤，再（若標記成功）移除
  `\Inbox`（封存）。
- 無法擷取網域的郵件留在收件匣不標記。
- 更新 SPEC.md、AGENTS.md、README.md 及 main.py（label_emails、
  docstring、argparse 說明）以描述新工作流程。

## [0.1.0] - 2026-09-30
- 標記方式從巢狀 `/`（`hk/gov/hko`）改為扁平 `-`（`hk-gov-hko`），
  避免 Gmail 自動建立空的父標籤。
- `domain_to_label` 現以 `-` 接合反轉網域各部分；`ensure_label` 建
  立單一標籤（無父標籤迴圈）。
- 更新 SPEC.md、AGENTS.md、README.md 及 main.py 以反映扁平標記規則。

## [0.0.3] - 2026-09-30
- 以 OpenCode 內建模型（`opencode/big-pickle`）取代 Google Gemini，
  透過 `opencode run` 子程序呼叫。免 API 金鑰、免信用卡。
- 自 requirements.txt 移除 `google-generativeai` 相依套件。
- 自 `.env.example` 移除 `GEMINI_API_KEY`；新增 `OPENCODE_MODEL`。
- 更新 README.md 與 AGENTS.md。

## [0.0.2] - 2026-09-30
- 修復 Python 3.12+ 的 SSL 錯誤：改為傳入
  `ssl.create_default_context()` 至 `IMAPClient`，而非依賴 imapclient
  預設值（其建立 `PROTOCOL_TLS_SERVER` context，不適用於客戶端連線）。

## [0.0.1] - 2026-09-30
- 以 IMAP + 應用程式密碼取代 Gmail API（OAuth2）：免 Google Cloud
  Console、免信用卡。
- 以 Google Gemini（Google AI Studio 免費方案）取代 OpenAI。
- 更新 requirements.txt、.env.example、README.md、AGENTS.md 以反映
  新的 IMAP + Gemini 方案。

## [0.0.0] - 2026-09-30
- Workflow-1 初始實作：Gmail OAuth2、巢狀網域標記、AI 主題分析輸出
  至 `themes-ai.json`。
- 新增 `commit.sh` 開發變更週期與無閘門自動合併 CI
  （`dev-001 -> dev -> main`）。
