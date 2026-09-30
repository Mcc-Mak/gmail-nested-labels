# AGENTS.md

This repo is greenfield. **`SPEC.md` is the authoritative source for all project logic** — read it before any change. Anything below repeats or sharpens rules from it that are easy to get wrong.

## Branch & CI flow

- Work happens on `dev-001` only. Do not commit directly to `dev` or `main`.
- Auto-merge is gateless and one-directional: `dev-001` -> `dev` -> `main` via `.github/workflows/auto-merge.yml`.
- The dev change cycle is standardized by `commit.sh` (or a `Makefile`): prompt for `CHANGELOG.md` semver entry -> stage -> commit -> push to `dev-001`. Do not bypass it.
- Commit message format is strict: `[{X.X.X}] {message}` with a detailed body. Version is semantic `major.minor.patch`.

## Core labeling rule (do not approximate)

- Take the sender domain, split on `.`, reverse the parts, join with `/` to form nested Gmail labels.
- Canonical example: `hko.gov.hk` -> label `hk/gov/hko`. Create missing parent/child labels via IMAP `CREATE` before assigning with `X-GM-LABELS`.
- This is the single most important correctness check for `main.py`.

## Security (hard rule)

- Never commit `.env`, `credentials.json`, `token.json`, or `venv/`. `.gitignore` must exclude all of them.
- Gmail access uses IMAP + App Password (stored in `.env` as `GMAIL_USER` / `GMAIL_APP_PASSWORD`). No OAuth2 `credentials.json` or `token.json` is used, but they remain git-ignored for safety.
- No AI API key is needed — thematic analysis uses the OpenCode built-in model (`big-pickle`) invoked via `opencode run`.

## Stack & deliverables

- Python, isolated with `venv`. Dependencies pinned in `requirements.txt`.
- Gmail access: **IMAP** (`imapclient`) with a Gmail App Password — no Google Cloud Console needed.
- AI thematic analysis: **OpenCode built-in model** (`opencode/big-pickle`) via `opencode run` subprocess — no API key, no credit card.
- Entry point is `main.py` (Workflow-1): IMAP connect -> fetch N latest Inbox emails -> nested-domain-label via `CREATE` + `X-GM-LABELS` -> OpenCode thematic analysis written to `themes-ai.json`.
- The AI thematic output file is named exactly `themes-ai.json`.
