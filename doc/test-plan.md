# Test Plan（測試計畫）

## 1. 測試策略

以 fake-client 邏輯測試驗證 `label_emails` 的批次處理與驗證邏輯，不依賴
真實 Gmail IMAP 連線。

## 2. 測試案例

### TC-01：`--no-archive` 模式不封存

| 項目 | 內容 |
|------|------|
| 前置條件 | FakeClient，郵件帶有 `\Inbox` + `OldLabel` |
| 步驟 | `label_emails(client, emails, archive=False)` |
| 預期結果 | `remove_gmail_labels` 未以 `["\\Inbox"]` 呼叫；標籤已套用；`OldLabel` 已清除；`\Inbox` 仍在 |
| 對應需求 | SR-6a, US-3 |

### TC-02：預設封存模式

| 項目 | 內容 |
|------|------|
| 前置條件 | FakeClient，郵件帶有 `\Inbox` + `OldLabel` |
| 步驟 | `label_emails(client, emails, archive=True)` |
| 預期結果 | `remove_gmail_labels` 以 `["\\Inbox"]` 呼叫；`\Inbox` 已移除；網域標籤已套用 |
| 對應需求 | SR-6, US-2 |

### TC-03：argparse `--no-archive` 旗標解析

| 項目 | 內容 |
|------|------|
| 步驟 | 傳入 `["--no-archive"]` 解析 |
| 預期結果 | `args.no_archive == True` |
| 步驟 | 傳入 `[]` 解析 |
| 預期結果 | `args.no_archive == False` |
| 對應需求 | SR-6a |

### TC-04：`domain_to_label` 轉換

| 項目 | 內容 |
|------|------|
| 步驟 | `domain_to_label("hko.gov.hk")` |
| 預期結果 | `"hk-gov-hko"` |
| 對應需求 | SR-4 |

### TC-05：`py_compile` 語法檢查

| 項目 | 內容 |
|------|------|
| 步驟 | `python -W error::SyntaxWarning -m py_compile main.py` |
| 預期結果 | 無錯誤 |
| 對應需求 | SN-1 |

## 3. 測試執行

```bash
source venv/bin/activate
# 語法檢查
python -W error::SyntaxWarning -m py_compile main.py
# 邏輯測試（fake-client）
PYTHONPATH=. python /tmp/opencode/test_no_archive.py
```

## 4. 手動驗收測試

| 編號 | 步驟 | 預期結果 |
|------|------|----------|
| AT-01 | `python main.py --no-archive -n 5` | 郵件已標記但留在收件匣 |
| AT-02 | `python main.py -n 5` | 郵件已標記且已封存 |
| AT-03 | 檢查 `themes-ai.json` | 每封郵件出現在一個主題中 |
| AT-04 | 推送到 `dev-001` | CI 自動合併至 `dev` -> `main` |
