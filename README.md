# Gmail automation: nested-domain labeling + AI thematic analysis

Workflow-1 (see `SPEC.md`): authenticate to Gmail, fetch the N latest Inbox
emails, assign nested labels derived from the reversed sender domain, then
group the emails by theme using an AI model and write the result to
`themes-ai.json`.

## Prerequisites

- Python 3.9+

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Gmail OAuth2 credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create (or select) a project and enable the **Gmail API**.
3. Configure the OAuth consent screen (type: External is fine for testing).
4. Under **APIs & Services > Credentials**, create an **OAuth client ID** of
   type **Desktop app**.
5. Download the JSON and save it as `credentials.json` in the repo root.

On first run, `main.py` opens a browser to authorize access and writes
`token.json` (refresh token) for subsequent runs.

> `credentials.json` and `token.json` are local-only and git-ignored. Never
> commit them.

## AI API key

Copy `.env.example` to `.env` and set your OpenAI API key:

```bash
cp .env.example .env
# edit .env
```

## Usage

```bash
source venv/bin/activate
python main.py               # uses EMAIL_COUNT from .env (default 10)
python main.py -n 25         # process the 25 latest Inbox emails
python main.py --model gpt-4o
```

Output: `themes-ai.json`.

### Labeling rule

The sender domain is split on `.`, reversed, and joined with `/` to form a
nested Gmail label. Example: `hko.gov.hk` -> `hk/gov/hko`. Missing parent and
child labels are created automatically before assignment.

## Dev workflow

All work happens on `dev-001`. Use the standardized change cycle script:

```bash
./commit.sh
```

It prompts for a `CHANGELOG.md` semantic-version entry, stages everything,
commits as `[{X.X.X}] {message}` with a detailed body, and pushes to
`dev-001`. That push triggers gateless auto-merge `dev-001 -> dev -> main`
via `.github/workflows/auto-merge.yml`.
