"""Workflow-1: Gmail nested-domain labeling + AI thematic analysis.

Steps:
  1. Authenticate to Gmail via OAuth2.
  2. Fetch the N latest Inbox emails.
  3. For each email, derive a nested Gmail label from the reversed sender
     domain (e.g. hko.gov.hk -> hk/gov/hko) and assign it, creating any
     missing parent/child labels first.
  4. Send the subjects and bodies to an AI model to group the emails by
     theme and write the result to themes-ai.json.
"""

import argparse
import base64
import json
import os
import re
import sys

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional until first run
    OpenAI = None

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
THEMES_FILE = "themes-ai.json"
DEFAULT_EMAIL_COUNT = 10
DEFAULT_MODEL = "gpt-4o-mini"


def authenticate_gmail():
    """Return an authenticated Gmail service client."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                sys.exit(
                    f"ERROR: {CREDENTIALS_FILE} not found. See README.md for "
                    "how to generate Gmail OAuth2 credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_latest_emails(service, n):
    """Fetch the N latest Inbox emails in full."""
    result = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], maxResults=n)
        .execute()
    )
    messages = result.get("messages", [])
    emails = []
    for msg in messages:
        data = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        emails.append(data)
    return emails


def get_header(headers, name):
    for header in headers:
        if header["name"].lower() == name.lower():
            return header.get("value", "")
    return ""


def extract_domain(from_header):
    """Extract the lowercase sender domain from a From header.

    Handles "Name <user@example.com>" and bare "user@example.com".
    """
    if not from_header:
        return ""
    match = re.search(r"<([^>]+)>", from_header)
    email = match.group(1) if match else from_header.strip()
    if "@" in email:
        domain = email.rsplit("@", 1)[1]
    else:
        domain = email
    return domain.strip().lower()


def domain_to_label(domain):
    """Reverse the domain parts and join with '/'.

    Canonical example: hko.gov.hk -> hk/gov/hko
    """
    parts = [p for p in domain.split(".") if p]
    return "/".join(reversed(parts))


def get_body(payload):
    """Return the plain-text body from a message payload."""

    def decode(data):
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    body = payload.get("body", {})
    if body.get("data"):
        return decode(body["data"])

    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return decode(part["body"]["data"])

    # Fallback: first part with any body data.
    for part in payload.get("parts", []) or []:
        if part.get("body", {}).get("data"):
            return decode(part["body"]["data"])
    return ""


class LabelManager:
    """Create and look up nested Gmail labels, caching the label table."""

    def __init__(self, service):
        self.service = service
        self.labels = {}
        self._refresh()

    def _refresh(self):
        self.labels = {}
        resp = self.service.users().labels().list(userId="me").execute()
        for label in resp.get("labels", []):
            self.labels[label["name"].lower()] = label["id"]

    def ensure(self, label_name):
        """Ensure label_name (and all parents) exist; return its id.

        Gmail auto-creates parent labels when a nested name is created, but
        we create each level explicitly for guaranteed correctness.
        """
        parts = label_name.split("/")
        full = ""
        label_id = None
        for i, _ in enumerate(parts):
            full = "/".join(parts[: i + 1])
            key = full.lower()
            if key in self.labels:
                label_id = self.labels[key]
                continue
            created = (
                self.service.users()
                .labels()
                .create(userId="me", body={"name": full})
                .execute()
            )
            label_id = created["id"]
            self.labels[key] = label_id
        return label_id


def label_emails(service, emails):
    """Assign reversed-domain nested labels to each email.

    Returns a list of (domain, label) for successfully labeled emails.
    """
    manager = LabelManager(service)
    labeled = []
    for msg in emails:
        headers = msg.get("payload", {}).get("headers", [])
        from_header = get_header(headers, "From")
        domain = extract_domain(from_header)
        if not domain:
            continue
        label_name = domain_to_label(domain)
        label_id = manager.ensure(label_name)
        service.users().messages().modify(
            userId="me",
            id=msg["id"],
            body={"addLabelIds": [label_id], "removeLabelIds": []},
        ).execute()
        labeled.append((domain, label_name))
        print(f"Labeled {msg['id']} -> {label_name}")
    return labeled


def build_ai_input(emails):
    """Build the list of subjects+bodies to send to the AI model."""
    items = []
    for i, msg in enumerate(emails, start=1):
        headers = msg.get("payload", {}).get("headers", [])
        subject = get_header(headers, "Subject")
        body = get_body(msg.get("payload", {}))
        from_header = get_header(headers, "From")
        items.append(
            {
                "index": i,
                "sender": from_header,
                "subject": subject,
                "body": body[:2000],
            }
        )
    return items


def thematic_analysis(email_items, api_key, model):
    """Ask the AI model to group emails by theme; return parsed JSON."""
    if OpenAI is None:
        sys.exit("ERROR: openai package not installed. Run: pip install -r requirements.txt")
    if not api_key:
        sys.exit("ERROR: OPENAI_API_KEY not set. Add it to .env.")

    client = OpenAI(api_key=api_key)
    user_content = json.dumps(email_items, ensure_ascii=False, indent=2)
    system_prompt = (
        "You are an assistant that groups emails by overarching theme. "
        "Given a JSON array of emails (each with index, sender, subject, body), "
        "categorize them into themes. Respond with ONLY valid JSON of the form: "
        '{"themes": [{"theme": "<name>", "description": "<short>", '
        '"emails": [{"index": <int>, "sender": "...", "subject": "..."}]}]}. '
        "Every input email must appear in exactly one theme."
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Gmail nested-domain labeling + AI themes.")
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=int(os.getenv("EMAIL_COUNT", DEFAULT_EMAIL_COUNT)),
        help="Number of latest Inbox emails to process (default: env EMAIL_COUNT or 10).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        help="OpenAI model for thematic analysis.",
    )
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY", "")

    print(f"Authenticating with Gmail...")
    service = authenticate_gmail()

    print(f"Fetching {args.count} latest Inbox emails...")
    emails = fetch_latest_emails(service, args.count)
    if not emails:
        print("No emails found.")
        return

    print("Assigning nested domain labels...")
    label_emails(service, emails)

    print(f"Running AI thematic analysis (model: {args.model})...")
    email_items = build_ai_input(emails)
    themes = thematic_analysis(email_items, api_key, args.model)

    with open(THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)
    print(f"Wrote thematic analysis to {THEMES_FILE}")


if __name__ == "__main__":
    main()
