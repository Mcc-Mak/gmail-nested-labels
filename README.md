# Gmail automation: nested-domain labeling + AI thematic analysis

Workflow-1 (see `SPEC.md`): connect to Gmail via IMAP, fetch the N latest
Inbox emails, assign nested labels derived from the reversed sender domain,
then group the emails by theme using Google Gemini and write the result to
`themes-ai.json`.

## Prerequisites

- Python 3.9+
- A Gmail account with **2-Step Verification** enabled
- A free **Google AI Studio** API key for Gemini

> **No Google Cloud Console or credit card needed.** Gmail access uses IMAP
> with an App Password; AI analysis uses the Gemini free tier.

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

## Gemini API key (free)

1. Go to **Google AI Studio**: https://aistudio.google.com/apikey
2. Click **Create API key**.
3. Copy the key.

> Google AI Studio is separate from Google Cloud Console — no project, no
> billing, no credit card required.

## Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
GEMINI_API_KEY=AIza...
```

> `.env` is git-ignored. Never commit it.

## Usage

```bash
source venv/bin/activate
python main.py               # uses EMAIL_COUNT from .env (default 10)
python main.py -n 25         # process the 25 latest Inbox emails
python main.py --model gemini-2.0-flash
```

Output: `themes-ai.json`.

### Labeling rule

The sender domain is split on `.`, reversed, and joined with `/` to form a
nested Gmail label. Example: `hko.gov.hk` -> `hk/gov/hko`. Missing parent
and child labels are created automatically before assignment via IMAP
`CREATE` + `X-GM-LABELS`.

## Dev workflow

All work happens on `dev-001`. Use the standardized change cycle script:

```bash
./commit.sh
```

It prompts for a `CHANGELOG.md` semantic-version entry, stages everything,
commits as `[{X.X.X}] {message}` with a detailed body, and pushes to
`dev-001`. That push triggers gateless auto-merge `dev-001 -> dev -> main`
via `.github/workflows/auto-merge.yml`.
