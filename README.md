# Gmail automation: flat-domain labeling + AI thematic analysis

Workflow-1 (see `SPEC.md`): connect to Gmail via IMAP, fetch the N latest
Inbox emails, assign a flat label derived from the reversed sender domain,
then group the emails by theme using the OpenCode built-in model and write
the result to `themes-ai.json`.

## Prerequisites

- Python 3.9+
- A Gmail account with **2-Step Verification** enabled
- **OpenCode** CLI installed (for thematic analysis — no API key needed)

> **No Google Cloud Console, no credit card, no API keys.** Gmail access
> uses IMAP with an App Password; AI analysis uses OpenCode's built-in free
> model (`big-pickle`).

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Gmail App Password

1. Enable **2-Step Verification** on your Google account:
   https://myaccount.google.com/security
2. Generate an **App Password** at:
   https://myaccount.google.com/apppasswords
   (Select "Mail" as the app, any name for the device.)
3. Copy the 16-character password.

## Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

> `.env` is git-ignored. Never commit it.

## Usage

```bash
source venv/bin/activate
python main.py               # uses EMAIL_COUNT from .env (default 10)
python main.py -n 25         # process the 25 latest Inbox emails
python main.py --model opencode/big-pickle
```

Output: `themes-ai.json`.

### Labeling rule

For each of the N latest Inbox emails the script: removes every existing
label except `Inbox` (clean slate); creates (if missing) and assigns a
single flat Gmail label derived from the reversed sender domain; then, if a
label was applied, removes the `Inbox` label to archive the email.

The sender domain is split on `.`, reversed, and joined with `-` to form a
single flat Gmail label. Example: `hko.gov.hk` -> `hk-gov-hko`. The label is
created if missing via IMAP `CREATE` + `X-GM-LABELS`. No `/` is used, so
Gmail does not auto-create empty parent labels. Emails with no extractable
domain stay in the Inbox unlabeled.

## Dev workflow

All work happens on `dev-001`. Use the standardized change cycle script:

```bash
./commit.sh
```

It prompts for a `CHANGELOG.md` semantic-version entry, stages everything,
commits as `[{X.X.X}] {message}` with a detailed body, and pushes to
`dev-001`. That push triggers gateless auto-merge `dev-001 -> dev -> main`
via `.github/workflows/auto-merge.yml`.
