以下是一份完整的提示詞，可直接複製貼到 AI 編碼助手以產生此一專案：

---

**系統角色與目標：**
你是一位資深 Python 開發者與 DevOps 工程師。我需要你產生一個基於 Python 的 Gmail 自動化專案的完整程式碼庫、設定檔與安裝說明，並配備嚴格的 Git/CI 工作流程。

**專案準則與硬性規定：**

1. **環境：** 專案必須以 Python 建置，並以 `venv` 隔離。請提供安裝指令與 `requirements.txt`。
2. **安全（關鍵）：** 絕不可將憑證、API 金鑰、token 或 `.env` 檔案提交到遠端儲存庫。你必須產生一份完善的 `.gitignore`，明確排除 `credentials.json`、`token.json`、`.env` 與 `venv/` 目錄。

**核心應用邏輯（Workflow-1）：**
撰寫一支 Python 腳本，執行下列工作流程：

1. **認證與登入：** 使用 Gmail API（OAuth2）安全地登入 Gmail 帳號。
2. **擷取郵件：** 從 `Inbox` 擷取最新 N 封郵件。
3. **網域式扁平標記（清除 -> 標記 -> 封存）：** 對每封擷取的郵件，先移除 `Inbox` 以外的所有現有標籤（乾淨狀態）。接著擷取寄件者網域，切分、反轉，並依此結構建立/指派單一扁平 Gmail 標籤。最後，若成功套用標籤，則移除 `Inbox` 標籤（封存）使郵件離開收件匣。無法擷取網域的郵件留在收件匣不標記。
* *規則：* 寄件者網域 `hko.gov.hk` 必須使郵件被指派到扁平標籤 `hk-gov-hko`。若該標該標籤不存在，腳本必須建立它。反轉後的各部分以 `-` 接合（不得用 `/`），以免 Gmail 自動建立空的父標籤。


4. **AI 主題分析：** 讀取這 N 封最新郵件的主旨與內文。將此資料傳給 AI 模型（例如透過 OpenAI API 或類似服務），依概括性主題將郵件分類分組。將此主題分析輸出到本地檔案 `themes-ai.json`。

**CI/CD 管線（GitHub Actions）：**
建立必要的 `.github/workflows/` YAML 檔案，以設置一條自動、無閘門的合併管線：

* 任何推送到 `dev-001` 分支的程式碼都必須自動觸發合併到 `dev` 分支。
* 成功合併到 `dev` 後必須自動觸發合併到 `main` 分支。
* 此流程不應有任何人工審批閘門。

**每次變更週期的開發者工作流程：**
提供一份 `Makefile` 或 bash 腳本（`commit.sh`），為開發者標準化下列變更週期工作流程：

1. **Changelog：** 提示開發者以語意化版本（`X.X.X` - major/minor/patch）更新 `CHANGELOG.md`，描述該次變更。
2. **Git 控制：** 暫存變更，並強制嚴格的提交訊息格式：`[{X.X.X}] {message}`，並附詳細提交內文。
3. **推送：** 自動將提交推送到 `dev-001` 分支。

**必要交付物：**

* `main.py`（包含 Workflow-1）
* `.gitignore`
* `requirements.txt`
* `.github/workflows/auto-merge.yml`
* `commit.sh`（或 `Makefile`）用於開發工作流程
* `README.md`，附上如何在本地產生初始 `credentials.json` 並設定 AI API 金鑰的說明。

請完整產生所有檔案，使其可直接複製貼到我的本地環境。
