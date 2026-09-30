# Schema（資料結構）

## 1. 郵件資料結構

### Email（擷取結果）

```json
{
  "uid": 12345,
  "raw": "<RFC822 bytes>"
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| `uid` | `int` | IMAP UID（單調遞增） |
| `raw` | `bytes` | RFC822 完整郵件原始位元組 |

---

## 2. AI 輸入結構

### AIInputItem

```json
{
  "index": 1,
  "sender": "Newsletter <news@example.com>",
  "subject": "本週電子報",
  "body": "郵件內文前 2000 字元..."
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| `index` | `int` | 序號（從 1 起） |
| `sender` | `str` | `From` 標頭 |
| `subject` | `str` | `Subject` 標頭 |
| `body` | `str` | 純文字內文（截斷至 2000 字元） |

---

## 3. AI 輸出結構（themes-ai.json）

### ThemesOutput

```json
{
  "themes": [
    {
      "theme": "電子報",
      "description": "定期訂閱電子報",
      "emails": [
        {
          "index": 1,
          "sender": "Newsletter <news@example.com>",
          "subject": "本週電子報"
        }
      ]
    }
  ]
}
```

| 欄位 | 型別 | 說明 |
|------|------|------|
| `themes` | `list[Theme]` | 主題清單 |

### Theme

| 欄位 | 型別 | 說明 |
|------|------|------|
| `theme` | `str` | 主題名稱 |
| `description` | `str` | 簡短描述 |
| `emails` | `list[ThemeEmail]` | 歸屬此主題的郵件 |

### ThemeEmail

| 欄位 | 型別 | 說明 |
|------|------|------|
| `index` | `int` | 原始序號 |
| `sender` | `str` | 寄件者 |
| `subject` | `str` | 主旨 |

---

## 4. 環境變數

```env
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
EMAIL_COUNT=10
OPENCODE_MODEL=opencode/big-pickle
```
