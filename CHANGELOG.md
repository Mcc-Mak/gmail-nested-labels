# Changelog

所有重要變更列於此處。版本遵循語意化版本（major.minor.patch）。

## [Unreleased]

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
