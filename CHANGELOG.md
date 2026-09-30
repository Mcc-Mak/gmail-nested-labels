# Changelog

All notable changes are listed here. Versions follow semantic versioning
(major.minor.patch).

## [Unreleased]

## [0.2.2] - 2026-09-30
- Hardened `auto-merge.yml` against intermittent `git push origin main`
  failures (HTTP 403 RPC errors seen on the 0.1.0 and 0.2.0 runs; 0.2.1
  succeeded, confirming the failure was transient).
- Added `concurrency` control (`cancel-in-progress: true`) so rapid
  successive pushes to `dev-001` no longer race two `merge-to-main` jobs
  against the same `main` ref.
- Added a 3-attempt retry loop (re-fetch + re-merge + retry) to both push
  steps to ride through transient RPC failures.

## [0.2.1] - 2026-09-30
- Fixed crash in `label_emails` (clear step): `get_gmail_labels` returns a
  dict `{uid: (labels,)}`, but the code iterated the dict itself, passing
  integer UIDs as labels into `remove_gmail_labels` -> `AttributeError`.
  Now extracts the label tuple for the message uid.

## [0.2.0] - 2026-09-30
- Workflow is now clear -> label -> archive: for each fetched email, remove
  every existing label except `\Inbox`, apply the flat domain label, then
  remove `\Inbox` (archive) if labeling succeeded.
- Emails with no extractable domain stay in the Inbox unlabeled.
- Updated SPEC.md, AGENTS.md, README.md, and main.py (label_emails, docstrings,
  argparse description) to describe the new workflow.

## [0.1.0] - 2026-09-30
- Switched labeling from nested `/` (`hk/gov/hko`) to flat `-` (`hk-gov-hko`)
  to avoid Gmail auto-creating empty parent labels.
- `domain_to_label` now joins reversed domain parts with `-`; `ensure_label`
  creates a single label (no parent loop).
- Updated SPEC.md, AGENTS.md, README.md, and main.py to reflect the flat
  labeling rule.

## [0.0.3] - 2026-09-30
- Replaced Google Gemini with OpenCode built-in model (`opencode/big-pickle`)
  via `opencode run` subprocess. No API key, no credit card needed.
- Removed `google-generativeai` dependency from requirements.txt.
- Removed `GEMINI_API_KEY` from `.env.example`; added `OPENCODE_MODEL`.
- Updated README.md and AGENTS.md accordingly.

## [0.0.2] - 2026-09-30
- Fixed SSL error on Python 3.12+: pass `ssl.create_default_context()` to
  `IMAPClient` instead of relying on imapclient's default (which creates a
  `PROTOCOL_TLS_SERVER` context, invalid for client connections).

## [0.0.1] - 2026-09-30
- Replaced Gmail API (OAuth2) with IMAP + App Password: no Google Cloud
  Console or credit card needed.
- Replaced OpenAI with Google Gemini (free tier via Google AI Studio).
- Updated requirements.txt, .env.example, README.md, and AGENTS.md to
  reflect the new IMAP + Gemini approach.

## [0.0.0] - 2026-09-30
- Initial implementation of Workflow-1: Gmail OAuth2, nested-domain labeling,
  and AI thematic analysis output to `themes-ai.json`.
- Added `commit.sh` dev change cycle and gateless auto-merge CI
  (`dev-001 -> dev -> main`).
