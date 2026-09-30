# RTM（需求追溯矩陣，Requirements Traceability Matrix）

本矩陣將需求（PRD/SRS）追溯至使用者故事、原始碼與測試。

| 需求編號 | 需求名稱 | 使用者故事 | 原始碼 | 驗證方式 |
|----------|----------|-----------|--------|----------|
| SR-1 | IMAP 連線 | US-1 | `connect_imap()` | 連線成功/失敗訊息 |
| SR-2 | 擷取最新 N 封郵件 | US-1 | `fetch_latest_emails()` | UID 列表非空 |
| SR-3 | 清除 `\Inbox` 以外標籤 | US-6 | `label_emails()` 清除步驟 | `get_gmail_labels` 驗證 |
| SR-4 | 扁平網域標籤轉換 | US-1 | `domain_to_label()` | `hko.gov.hk` -> `hk-gov-hko` |
| SR-5 | `CREATE` + `X-GM-LABELS` 套用 | US-1 | `ensure_label()` + `add_gmail_labels()` | 重新擷取標籤驗證 |
| SR-6 | 封存（移除 `\Inbox`） | US-2 | `label_emails(archive=True)` | `\Inbox` 不存在 |
| SR-6a | `--no-archive` 除錯模式 | US-3 | `label_emails(archive=False)` | 標籤已套用、`\Inbox` 仍在 |
| SR-7 | 驗證 `X-GM-LABELS` | US-2, US-3 | `label_emails()` 驗證步驟 | 逐 UID 回報 |
| SR-8 | AI 主題分析 | US-4 | `thematic_analysis()` | `themes-ai.json` 產出 |
| SR-9 | 無網域郵件留在收件匣 | US-5 | `label_emails()` 跳過邏輯 | 輸出提示訊息 |
| FR-7 | CI/CD 自動合併 | — | `auto-merge.yml` | CI 綠燈 |
