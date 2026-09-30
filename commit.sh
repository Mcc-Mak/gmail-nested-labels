#!/usr/bin/env bash
# Standardized dev change cycle:
#   1. Prompt for a CHANGELOG.md semantic-version entry.
#   2. Stage all changes.
#   3. Commit with the strict format: [{X.X.X}] {message} + detailed body.
#   4. Push to dev-001 (triggers gateless auto-merge dev-001 -> dev -> main).
set -euo pipefail

BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" != "dev-001" ]; then
  echo "ERROR: must run on dev-001 (current: $BRANCH)." >&2
  exit 1
fi

CHANGELOG="CHANGELOG.md"
touch "$CHANGELOG"

echo "== Changelog =="
read -r -p "Semantic version (X.X.X): " VERSION
if ! echo "$VERSION" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: invalid version '$VERSION'. Expected major.minor.patch." >&2
  exit 1
fi

read -r -p "Changelog summary: " CHANGE_MSG

# Prepend the new entry.
TMP=$(mktemp)
{
  echo "## [$VERSION] - $(date +%Y-%m-%d)"
  echo "- $CHANGE_MSG"
  echo ""
  cat "$CHANGELOG"
} > "$TMP"
mv "$TMP" "$CHANGELOG"

echo "== Commit =="
git add -A
read -r -p "Commit subject (without version prefix): " COMMIT_SUBJECT
echo "Detailed commit body (end with a line containing only 'END'):"
COMMIT_BODY=""
while IFS= read -r line; do
  [ "$line" = "END" ] && break
  COMMIT_BODY="${COMMIT_BODY}${line}"$'\n'
done

if [ -n "$COMMIT_BODY" ]; then
  git commit -m "[$VERSION] $COMMIT_SUBJECT" -m "$COMMIT_BODY"
else
  git commit -m "[$VERSION] $COMMIT_SUBJECT"
fi

echo "== Push =="
git push origin dev-001
echo "Pushed [$VERSION] $COMMIT_SUBJECT to dev-001."
