# Project Charter（專案章程）

## 專案名稱

Gmail 自動化：扁平網域標記 + AI 主題分析

## 專案摘要

以 Python 自動化 Gmail 郵件分類：透過 IMAP 連線 Gmail，擷取最新收件匣
郵件，依寄件者網域自動套用扁平標籤並封存，再以 OpenCode 內建 AI 模型
進行主題分析。

## 目標

1. 自動將收件匣郵件依寄件者網域分類至扁平 Gmail 標籤。
2. 維持收件匣清爽（封存已標記郵件）。
3. 以 AI 模型對郵件進行主題分組，產出 `themes-ai.json`。

## 範圍

- **包含**：IMAP 連線、郵件擷取、清除/標記/封存、AI 主題分析、CI/CD
  自動合併管線。
- **不包含**：OAuth2 認證、Google Cloud Console 設定、付費 API 服務。

## 技術方案

- Gmail 存取：IMAP + 應用程式密碼（免 Google Cloud Console）。
- AI 分析：OpenCode 內建模型 `opencode/big-pickle`（免 API 金鑰）。
- CI/CD：GitHub Actions 無閘門自動合併 `dev-001 -> dev -> main`。

## 利害關係人

- 開發者：負責在 `dev-001` 上開發並透過 `commit.sh` 提交。
- 最終使用者：透過 Gmail 帳號收發郵件的使用者。

## 限制

- 需啟用 Gmail 兩步驟驗證以產生應用程式密碼。
- Gmail IMAP 有速率限制，批次處理以減少往返次數。
