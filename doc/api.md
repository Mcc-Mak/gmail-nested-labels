# API 文件

本文檔描述 `main.py` 各函式的介面規格。

## `connect_imap(user, app_password) -> IMAPClient`

連線並登入 Gmail IMAP。

| 參數 | 型別 | 說明 |
|------|------|------|
| `user` | `str` | Gmail 帳號 |
| `app_password` | `str` | 應用程式密碼 |

**回傳**：`IMAPClient` 實例

**例外**：`SystemExit` — 若 `user` 或 `app_password` 為空。

---

## `fetch_latest_emails(client, n) -> list[dict]`

擷取最新 N 封收件匣郵件完整內容。

| 參數 | 型別 | 說明 |
|------|------|------|
| `client` | `IMAPClient` | 已連線的 IMAP 客戶端 |
| `n` | `int` | 擷取封數 |

**回傳**：`[{"uid": int, "raw": bytes}, ...]`

---

## `extract_domain(from_header) -> str`

從 `From` 標頭擷取小寫寄件者網域。

| 參數 | 型別 | 說明 |
|------|------|------|
| `from_header` | `str` | 郵件 `From` 標頭 |

**回傳**：小寫網域字串，無法擷取時回傳 `""`。

---

## `domain_to_label(domain) -> str`

反轉網域各部分並以 `-` 接合。

| 參數 | 型別 | 說明 |
|------|------|------|
| `domain` | `str` | 網域（如 `hko.gov.hk`） |

**回傳**：扁平標籤（如 `hk-gov-hko`）

---

## `ensure_label(client, label_name) -> None`

以 IMAP `CREATE` 建立標籤（若不存在）。Gmail 將 `-` 和 `/` 視為等價，
故 `CREATE "com-github"` 在 `"com/github"` 已存在時傳回 `ALREADYEXISTS`。
此函式在偵測到此衝突時，刪除舊 `/` 格式標籤後重試 `CREATE`。若刪除
傳回 `NONEXISTENT`，表示 `-` 格式標籤已正確存在，直接返回。其他錯誤
重新拋出。

| 參數 | 型別 | 說明 |
|------|------|------|
| `client` | `IMAPClient` | IMAP 客戶端 |
| `label_name` | `str` | 標籤名稱 |

---

## `get_body(msg) -> str`

從 `email.message.Message` 擷取純文字內文。

| 參數 | 型別 | 說明 |
|------|------|------|
| `msg` | `email.message.Message` | 郵件物件 |

**回傳**：純文字內文字串

---

## `label_emails(client, emails, archive=True) -> None`

核心流程：清除 -> 標記 -> 封存 -> 驗證（批次處理）。

封存方式為 `STORE +FLAGS \Deleted` + `UID EXPUNGE`（從 INBOX 移除即等同
Gmail 封存，使用者標籤保留在「全部郵件」中）。驗證分兩階段：封存前以
`get_gmail_labels` 檢查標籤是否套用，封存後以 `search("ALL")` 確認
UID 已不在 INBOX。

| 參數 | 型別 | 預設 | 說明 |
|------|------|------|------|
| `client` | `IMAPClient` | — | IMAP 客戶端 |
| `emails` | `list[dict]` | — | `fetch_latest_emails` 回傳的郵件清單 |
| `archive` | `bool` | `True` | 是否封存（`False` = 除錯模式） |

---

## `build_ai_input(emails) -> list[dict]`

建構要傳給 AI 模型的主旨+內文清單。

| 參數 | 型別 | 說明 |
|------|------|------|
| `emails` | `list[dict]` | 郵件清單 |

**回傳**：`[{"index", "sender", "subject", "body"}, ...]`

---

## `thematic_analysis(email_items, model) -> dict`

呼叫 OpenCode 模型進行主題分析。

| 參數 | 型別 | 說明 |
|------|------|------|
| `email_items` | `list[dict]` | `build_ai_input` 回傳值 |
| `model` | `str` | 模型名稱（如 `opencode/big-pickle`） |

**回傳**：`{"themes": [{"theme", "description", "emails": [...]}, ...]}`

---

## `main() -> None`

程式進入點。解析 CLI 參數、連線 IMAP、執行標記與主題分析。

**CLI 參數**：

| 參數 | 說明 | 預設 |
|------|------|------|
| `-n` / `--count` | 處理郵件數 | `EMAIL_COUNT` 或 `10` |
| `--model` | AI 模型 | `OPENCODE_MODEL` 或 `opencode/big-pickle` |
| `--no-archive` | 除錯模式（不封存） | `False` |
