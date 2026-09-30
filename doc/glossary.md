# Glossary（詞彙表）

本專案使用的專有名詞與縮寫對照表。

| 詞彙 | 英文 | 說明 |
|------|------|------|
| 扁平標籤 | Flat Label | 以 `-` 接合反轉網域各部分所構成的 Gmail 標籤，如 `hk-gov-hko` |
| 應用程式密碼 | App Password | Google 帳號用於非瀏覽器登入的 16 字元密碼，需先啟用兩步驟驗證 |
| 清除 | Clear | 移除郵件上 `\Inbox` 以外的所有現有標籤 |
| 標記 | Label | 以 `X-GM-LABELS` 套用扁平網域標籤至郵件 |
| 封存 | Archive | 移除 `\Inbox` 標籤使郵件離開收件匣 |
| 除錯模式 | Debug Mode | `--no-archive` 旗標，跳過封存步驟以便檢驗標籤 |
| 主題分析 | Thematic Analysis | 以 AI 模型將郵件依主題分組 |
| IMAP | Internet Message Access Protocol | 郵件存取協定，本專案用於 Gmail 連線 |
| `X-GM-LABELS` | Gmail Labels | Gmail IMAP 擴充指令，用於讀取/設定 Gmail 標籤 |
| `\Inbox` | Inbox Flag | IMAP 系統旗標，代表郵件位於收件匣 |
| `RFC822` | RFC 822 | 郵件格式標準，用於完整擷取郵件內容 |
| 無閘門合併 | Gateless Merge | CI 自動合併流程，無需人工審批 |
| 語意化版本 | Semantic Versioning | `major.minor.patch` 版本編號規範 |
