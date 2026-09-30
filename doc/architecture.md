# Architecture（架構文件）

## 1. 系統概觀

本系統為單一 Python 腳本（`main.py`），執行 Gmail IMAP 郵件標記與 AI
主題分析。無持久層、無伺服器，為一次性命令列工具。

## 2. 元件

| 元件 | 說明 |
|------|------|
| `connect_imap()` | 以 IMAP + 應用程式密碼連線 Gmail |
| `fetch_latest_emails()` | 擷取最新 N 封收件匣郵件（RFC822） |
| `extract_domain()` / `domain_to_label()` | 網域擷取與扁平標籤轉換 |
| `ensure_label()` | 以 IMAP `CREATE` 建立標籤；`ALREADYEXISTS`時刪除舊 `/` 格式標籤後重試 |
| `label_emails()` | 核心流程：清除 -> 標記 -> 封存 -> 驗證 |
| `build_ai_input()` | 建構 AI 輸入資料 |
| `thematic_analysis()` | 呼叫 `opencode run` 進行主題分析 |

## 3. IMAP 互動時序

```mermaid
sequenceDiagram
    participant M as main.py
    participant I as Gmail IMAP
    participant O as opencode run

    M->>I: login(user, app_password)
    I-->>M: OK
    M->>I: select_folder("INBOX")
    M->>I: search("ALL")
    I-->>M: [uid1, uid2, ...]
    M->>I: fetch(latest_n, ["RFC822"])
    I-->>M: {uid: {b"RFC822": raw}}

    loop 逐封郵件
        M->>M: extract_domain(from_header)
        M->>M: domain_to_label(domain)
    end

    M->>I: get_gmail_labels(target_uids)
    I-->>M: {uid: (labels,)}

    loop 逐 UID 清除
        M->>I: remove_gmail_labels(uid, [非 \\Inbox 標籤])
    end

    loop 依標籤分組
        M->>I: create_folder(label_name)
        alt OK
            I-->>M: OK
        else ALREADYEXISTS（舊 '/' 格式衝突）
            I-->>M: ALREADYEXISTS
            M->>I: delete_folder(slash_name)
            I-->>M: OK
            M->>I: create_folder(label_name)
            I-->>M: OK
        end
        M->>I: add_gmail_labels(uids, [label_name])
        opt archive=True（預設）
            M->>I: remove_gmail_labels(uids, ["\\Inbox"])
        end
    end

    M->>I: get_gmail_labels(target_uids)
    I-->>M: {uid: (labels,)}
    M->>M: 驗證 has_label / not in_inbox
    M->>I: logout()

    M->>O: opencode run -m big-pickle（郵件資料以檔案附加）
    O-->>M: JSON {themes: [...]}
    M->>M: 寫入 themes-ai.json
```

## 4. 標記工作流程

```mermaid
flowchart TD
    A[開始] --> B[擷取最新 N 封郵件]
    B --> C{逐封解析}
    C -->|有網域| D[domain_to_label]
    C -->|無網域| E[留在收件匣不標記]
    D --> F[收集目標 UID]
    F --> G[get_gmail_labels 一次擷取]
    G --> H[逐 UID 移除非 \\Inbox 標籤]
    H --> I[依標籤分組]
    I --> J{逐標籤}
    J --> K[ensure_label: CREATE 或衝突清理]
    K --> L[add_gmail_labels]
    L --> M{archive?}
    M -->|是| N[remove_gmail_labels \\Inbox]
    M -->|否| O[跳過封存]
    N --> P[驗證: 重新擷取 X-GM-LABELS]
    O --> P
    P --> Q{驗證結果}
    Q -->|標籤已套用 且 已封存| R[成功]
    Q -->|否| S[回報失敗]
    R --> T[AI 主題分析]
    S --> T
    E --> T
```

## 5. CI/CD 流程

```mermaid
flowchart LR
    A[dev-001 push] --> B[merge-to-dev job]
    B -->|git merge| C[dev branch]
    C --> D[merge-to-main job]
    D -->|git merge| E[main branch]
    B -.->|3 次重試| B
    D -.->|3 次重試| D
```
