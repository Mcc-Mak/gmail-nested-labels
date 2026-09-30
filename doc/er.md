# ER（實體關係圖）

## 資料實體關係

```mermaid
erDiagram
    EMAIL ||--o{ LABEL : has
    EMAIL ||--|| DOMAIN : from
    DOMAIN ||--|| FLAT_LABEL : maps_to
    EMAIL ||--o{ THEME : belongs_to
    THEME ||--|{ THEME_EMAIL : contains

    EMAIL {
        int uid PK
        bytes raw
        string from_header
        string subject
    }

    LABEL {
        string name PK
        bool is_inbox
    }

    DOMAIN {
        string domain PK
        string reversed_parts
    }

    FLAT_LABEL {
        string label_name PK
        string create_command
    }

    THEME {
        string theme_name PK
        string description
    }

    THEME_EMAIL {
        int index PK
        string sender
        string subject
    }
```

## 實體說明

| 實體 | 說明 |
|------|------|
| `EMAIL` | 擷取的郵件，含 UID 與原始內容 |
| `LABEL` | Gmail 標籤（含系統標籤 `\Inbox`） |
| `DOMAIN` | 寄件者網域，切分後反轉 |
| `FLAT_LABEL` | 扁平標籤，由 `DOMAIN` 映射而來 |
| `THEME` | AI 主題分析的主題分組 |
| `THEME_EMAIL` | 歸屬某主題的郵件摘要 |
