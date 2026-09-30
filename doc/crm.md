# CRM（交叉參照矩陣，Cross-Reference Matrix）

本矩陣記錄各文件、程式碼與設定檔之間的交叉參照關係。

## 文件 ↔ 程式碼

| 文件 | 參照目標 | 說明 |
|------|----------|------|
| `SPEC.md` | `main.py` | 規格定義 Workflow-1 |
| `AGENTS.md` | `main.py`, `commit.sh`, `auto-merge.yml` | 開發準則與核心規則 |
| `doc/architecture.md` | `main.py` | 元件與時序圖 |
| `doc/api.md` | `main.py` 各函式 | 函式介面規格 |
| `doc/schema.md` | `themes-ai.json`, `.env` | 資料結構定義 |
| `doc/srs.md` | `main.py`, `auto-merge.yml` | 系統需求 |
| `doc/adr.md` | `main.py`, `requirements.txt`, `.env.example` | 架構決策 |
| `doc/test-plan.md` | `main.py` | 測試案例 |
| `doc/quick-start.md` | `main.py`, `.env.example` | 快速入門 |

## 程式碼 ↔ 設定檔

| 程式碼 | 設定檔 | 說明 |
|--------|--------|------|
| `main.py` | `.env` | 環境變數載入 |
| `main.py` | `requirements.txt` | 相依套件 |
| `commit.sh` | `CHANGELOG.md` | 版本歷史 |
| `auto-merge.yml` | `.github/workflows/` | CI 設定 |

## 文件 ↔ 文件

| 來源 | 目標 | 說明 |
|------|------|------|
| `README.md` | `TOCTREE.md` | 文件索引入口 |
| `TOCTREE.md` | `doc/*.md` | 目錄樹 |
| `doc/rtm.md` | `doc/prd.md`, `doc/srs.md`, `doc/user-stories.md` | 需求追溯 |
| `doc/srs.md` | `doc/architecture.md` | 需求對應架構 |
| `doc/architecture.md` | `doc/adr.md` | 架構對應決策 |
