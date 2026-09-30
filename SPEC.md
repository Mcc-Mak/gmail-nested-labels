Here is a comprehensive prompt you can copy and paste into an AI coding assistant to generate this exact project:

---

**System Role & Objective:**
You are an expert Python developer and DevOps engineer. I need you to generate the complete codebase, configuration files, and setup instructions for a Python-based Gmail automation project with a strict Git/CI workflow.

**Project Guidelines & Hard Rules:**

1. **Environment:** The project must be built using Python and isolated via `venv`. Provide the setup commands and a `requirements.txt`.
2. **Security (CRITICAL):** Never commit credentials, API keys, tokens, or `.env` files to the remote repository. You must generate a robust `.gitignore` file that explicitly excludes `credentials.json`, `token.json`, `.env`, and the `venv/` directory.

**Core Application Logic (Workflow-1):**
Write a Python script that executes the following workflow:

1. **Authenticate & Login:** Securely log in to a Gmail account using the Gmail API (OAuth2).
2. **Fetch Emails:** Retrieve the N-th latest emails from the `Inbox`.
3. **Domain-Based Flat Labeling (clear -> label -> archive):** For each fetched email, first remove every existing label except `Inbox` (clean slate). Then extract the sender's email domain, split it, reverse it, and create/assign a single flat Gmail label based on this structure. Finally, if a label was applied successfully, remove the `Inbox` label (archive) so the email leaves the Inbox. Emails with no extractable domain stay in the Inbox unlabeled.
* *Rule:* A sender domain of `hko.gov.hk` must result in the email being assigned to the flat label `hk-gov-hko`. If the label does not exist, the script must create it. Reversed parts are joined with `-` (not `/`) to avoid Gmail auto-creating empty parent labels.


4. **AI Thematic Analysis:** Read the subjects and bodies of these N latest emails. Pass this data to an AI model (e.g., via OpenAI API or similar) to categorize and group the emails by overarching themes. Output this thematic analysis locally to a file named `themes-ai.json`.

**CI/CD Pipeline (GitHub Actions):**
Create the necessary `.github/workflows/` YAML files to establish an automatic, gateless merge pipeline:

* Any code pushed to the `dev-001` branch must automatically trigger a merge into the `dev` branch.
* A successful merge into `dev` must automatically trigger a merge into the `main` branch.
* There should be no manual approval gates for this flow.

**Developer Workflow per Change Cycle:**
Provide a `Makefile` or a bash script (`commit.sh`) that standardizes the following change cycle workflow for the developer:

1. **Changelog:** Prompts the developer to update `CHANGELOG.md` with a semantic version (`X.X.X` - major/minor/patch) describing the change.
2. **Git Control:** Stages the changes and enforces the strict commit message format: `[{X.X.X}] {message}` along with a detailed commit body.
3. **Push:** Automatically pushes the commit to the `dev-001` branch.

**Required Deliverables:**

* `main.py` (containing Workflow-1)
* `.gitignore`
* `requirements.txt`
* `.github/workflows/auto-merge.yml`
* `commit.sh` (or `Makefile`) for the dev workflow
* `README.md` with instructions on how to generate the initial `credentials.json` for Gmail and set up the AI API key locally.

Please generate all files completely, ready to be copied and pasted into my local environment.