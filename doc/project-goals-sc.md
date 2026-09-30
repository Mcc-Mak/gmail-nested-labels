# Project Goals (G) & Success Criteria (SC)

## 專案目標

| 編號 | 目標 | 說明 |
|------|------|------|
| G-1 | 自動分類郵件 | 依寄件者網域自動套用扁平 Gmail 標籤 |
| G-2 | 保持收件匣清爽 | 已標記郵件自動封存（移除 `\Inbox`） |
| G-3 | 免費無門檻 | 免 Google Cloud Console、免 API 金鑰、免信用卡 |
| G-4 | AI 主題分析 | 以 OpenCode 內建模型將郵件依主題分組 |
| G-5 | 自動化 CI/CD | 推送到 `dev-001` 後自動合併至 `dev` -> `main` |
| G-6 | 繁體中文化 | 全專案文件與使用者面向文字使用繁體中文 |

## 成功準則

| 編號 | 準則 | 對應目標 | 驗證方式 |
|------|------|----------|----------|
| SC-1 | `hko.gov.hk` -> `hk-gov-hko` 標籤正確建立並套用 | G-1 | 重新擷取 `X-GM-LABELS` 驗證 |
| SC-2 | 標記後 `\Inbox` 已移除（封存模式） | G-2 | `get_gmail_labels` 確認 `\Inbox` 不存在 |
| SC-3 | `--no-archive` 模式下郵件留在收件匣但標籤已套用 | G-2 | 驗證 `has_label=True` 且 `in_inbox=True` |
| SC-4 | 無 Google Cloud Console 設定、無 API 金鑰 | G-3 | 僅需 `.env` 中的 `GMAIL_USER` / `GMAIL_APP_PASSWORD` |
| SC-5 | `themes-ai.json` 產出且每封郵件出現在一個主題中 | G-4 | 檢查 JSON 結構 |
| SC-6 | 推送到 `dev-001` 後 CI 自動合併至 `main` | G-5 | GitHub Actions 綠燙 |
| SC-7 | 所有 `.md` 文件與 CLI 輸出為繁體中文 | G-6 | 人工檢視 |
| SC-8 | 舊標籤正確清除（僅剩 `\Inbox` + 網域標籤） | G-1 | `get_gmail_labels` 驗證 |
| SC-9 | 無網域的郵件留在收件匣不標記 | G-1 | 輸出提示訊息 |
| SC-10 | 批次處理，100 封郵件 IMAP 往返 < 20 次 | G-1 | 計算 `CREATE` + `add` + `remove` 呼叫次數 |
