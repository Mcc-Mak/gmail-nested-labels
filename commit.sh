#!/usr/bin/env bash
# 標準化開發變更週期：
#   1. 提示輸入 CHANGELOG.md 的語意化版本項目。
#   2. 暫存所有變更。
#   3. 以嚴格格式提交：[{X.X.X}] {message} + 詳細內文。
#   4. 推送到 dev-001（觸發無閘門自動合併 dev-001 -> dev -> main）。
set -euo pipefail

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$BRANCH" != "dev-001" ]]; then
  echo "錯誤：必須在 dev-001 上執行（目前：$BRANCH）。" >&2
  exit 1
fi

CHANGELOG="CHANGELOG.md"
touch "$CHANGELOG"

echo "== Changelog =="
read -r -p "語意化版本（X.X.X）: " VERSION
if ! echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "錯誤：無效的版本號 '$VERSION'。預期格式為 major.minor.patch。" >&2
  exit 1
fi

read -r -p "Changelog 摘要: " CHANGE_MSG

# 將新項目插入檔首。
TMP=$(mktemp)
{
  echo "## [$VERSION] - $(date +%Y-%m-%d)"
  echo "- $CHANGE_MSG"
  echo ""
  cat "$CHANGELOG"
} > "$TMP"
mv "$TMP" "$CHANGELOG"

echo "== 提交 =="
git add -A
read -r -p "提交主旨（不含版本前綴）: " COMMIT_SUBJECT
echo "詳細提交內文（以僅含 'END' 的行結束）:"
COMMIT_BODY=""
while IFS= read -r line; do
  [[ "$line" == "END" ]] && break
  COMMIT_BODY="${COMMIT_BODY}${line}"$'\n'
done

if [[ -n "$COMMIT_BODY" ]]; then
  git commit -m "[$VERSION] $COMMIT_SUBJECT" -m "$COMMIT_BODY"
else
  git commit -m "[$VERSION] $COMMIT_SUBJECT"
fi

echo "== 推送 =="
git push origin dev-001
echo "已推送 [$VERSION] $COMMIT_SUBJECT 到 dev-001。"
