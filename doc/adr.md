# ADR（架構決策記錄）

## ADR-001：使用 IMAP + 應用程式密碼取代 OAuth2

**狀態**：已接受

**背景**：最初規格要求使用 Gmail API（OAuth2），需要 Google Cloud
Console 設定、`credentials.json`、`token.json`。

**決策**：改用 IMAP + 應用程式密碼。

**原因**：
- 免 Google Cloud Console 設定。
- 免 OAuth2 token 管理與刷新。
- 僅需 `.env` 中的 `GMAIL_USER` / `GMAIL_APP_PASSWORD`。
- IMAP 原生支援 `X-GM-LABELS` 存取 Gmail 標籤。

**後果**：
- 需啟用兩步驟驗證以產生應用程式密碼。
- `.gitignore` 仍排除 `credentials.json` / `token.json` 以防萬一。

---

## ADR-002：扁平標籤（`-`）取代巢狀標籤（`/`）

**狀態**：已接受

**背景**：最初使用巢狀標籤（`hk/gov/hko`），但 Gmail 會自動建立空的
父標籤（`hk`、`hk/gov`）。

**決策**：改用扁平標籤，以 `-` 接合反轉網域各部分（`hk-gov-hko`）。

**原因**：
- 避免 Gmail 自動建立空的父標籤。
- 單一 IMAP `CREATE` 即可建立標籤，無需父標籤迴圈。

**後果**：
- 標籤為扁平字串，無階層結構。
- `domain_to_label` 以 `-` 接合反轉各部分。

---

## ADR-003：使用 OpenCode 內建模型取代付費 API

**狀態**：已接受

**背景**：最初使用 OpenAI API，後改用 Google Gemini，均需 API 金鑰。

**決策**：改用 OpenCode 內建模型 `opencode/big-pickle`，透過
`opencode run` 子程序呼叫。

**原因**：
- 免 API 金鑰、免信用卡。
- 利用 OpenCode CLI 已內建的模型。

**後果**：
- 需已安裝 `opencode` CLI。
- AI 輸出解析需處理 `opencode run --format json` 的事件串流格式。

---

## ADR-004：清除 -> 標記 -> 封存工作流程

**狀態**：已接受

**背景**：最初僅標記，不移除舊標籤，導致郵件帶有多個衝突標籤。

**決策**：工作流程改為清除（移除 `\Inbox` 以外所有標籤）-> 標記（套用
扁平網域標籤）-> 封存（移除 `\Inbox`）。

**原因**：
- 確保每封郵件僅帶有一個網域標籤。
- 封存使收件匣保持清爽。

**後果**：
- 新增 `--no-archive` 旗標以支援除錯模式（僅清除並標記，不封存）。
- 驗證邏輯需區分封存/除錯模式。

---

## ADR-005：批次處理與驗與驗證

**狀態**：已接受

**背景**：`label_emails` 逐 UID 處理（100 封郵件約 300 次 IMAP 往返），
且 `ensure_label` 吞掉所有錯誤，導致靜默 no-op。

**決策**：以標籤為單位批次處理（每組一次 `CREATE` + 一次
`add_gmail_labels` + 一次 `remove_gmail_labels`），並重新擷取
`X-GM-LABELS` 驗證結果。

**原因**：
- 減少 IMAP 伺服器往返，避免速率限制。
- `ensure_label` 僅容忍 `ALREADYEXISTS`，其他錯誤重新拋出。
- 驗證確保標籤確實套用、`\Inbox` 確實移除。

**後果**：
- 失敗以逐 UID 回報，不再虛報成功。
