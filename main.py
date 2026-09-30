"""Workflow-1: Gmail nested-domain labeling + AI thematic analysis.

Uses IMAP with a Gmail App Password (no Google Cloud Console needed) and
Google Gemini (free tier via Google AI Studio) for thematic analysis.

Steps:
  1. Connect to Gmail via IMAP using an App Password.
  2. Fetch the N latest Inbox emails.
  3. For each email, derive a nested Gmail label from the reversed sender
     domain (e.g. hko.gov.hk -> hk/gov/hko) and assign it, creating any
     missing parent/child labels first via IMAP CREATE.
  4. Send the subjects and bodies to Gemini to group the emails by theme
     and write the result to themes-ai.json.
"""

import argparse
import email
from email import policy
import json
import os
import re
import sys

from dotenv import load_dotenv
from imapclient import IMAPClient
import google.generativeai as genai

IMAP_HOST = "imap.gmail.com"
THEMES_FILE = "themes-ai.json"
DEFAULT_EMAIL_COUNT = 10
DEFAULT_MODEL = "gemini-1.5-flash"


def connect_imap(user, app_password):
    """Connect and login to Gmail IMAP; return an IMAPClient."""
    if not user or not app_password:
        sys.exit(
            "ERROR: GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env.\n"
            "See README.md for how to generate an App Password."
        )
    client = IMAPClient(IMAP_HOST, ssl=True)
    client.login(user, app_password)
    return client


def fetch_latest_emails(client, n):
    """Fetch the N latest Inbox emails in full (RFC822).

    Returns a list of dicts: {"uid": int, "raw": bytes}.
    UIDs are monotonically increasing, so the last N are the most recent.
    """
    client.select_folder("INBOX")
    uids = client.search("ALL")
    if not uids:
        return []
    latest = uids[-n:] if n < len(uids) else uids
    response = client.fetch(latest, ["RFC822"])
    emails = []
    for uid in latest:
        raw = response[uid][b"RFC822"]
        emails.append({"uid": uid, "raw": raw})
    return emails


def extract_domain(from_header):
    """Extract the lowercase sender domain from a From header.

    Handles "Name <user@example.com>" and bare "user@example.com".
    """
    if not from_header:
        return ""
    match = re.search(r"<([^>]+)>", from_header)
    addr = match.group(1) if match else from_header.strip()
    if "@" in addr:
        domain = addr.rsplit("@", 1)[1]
    else:
        domain = addr
    return domain.strip().lower()


def domain_to_label(domain):
    """Reverse the domain parts and join with '/'.

    Canonical example: hko.gov.hk -> hk/gov/hko
    """
    parts = [p for p in domain.split(".") if p]
    return "/".join(reversed(parts))


def ensure_label(client, label_name):
    """Create label_name and all parent labels via IMAP CREATE.

    Gmail maps IMAP folder creation to label creation. The '/' separator
    creates nested labels. We create each level explicitly for guaranteed
    correctness. Errors (label already exists) are silently ignored.
    """
    parts = label_name.split("/")
    full = ""
    for i in range(len(parts)):
        full = "/".join(parts[: i + 1])
        try:
            client.create_folder(full)
            print(f"  Created label: {full}")
        except Exception:
            pass


def get_body(msg):
    """Extract the plain-text body from an email.message.Message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_content()
                except Exception:
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode("utf-8", errors="replace")
        for part in msg.walk():
            if part.get_content_type().startswith("text/"):
                try:
                    return part.get_content()
                except Exception:
                    pass
        return ""
    try:
        return msg.get_content()
    except Exception:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""


def label_emails(client, emails):
    """Assign reversed-domain nested labels to each email via X-GM-LABELS."""
    for item in emails:
        msg = email.message_from_bytes(item["raw"], policy=policy.default)
        from_header = msg["From"] or ""
        domain = extract_domain(from_header)
        if not domain:
            continue
        label_name = domain_to_label(domain)
        ensure_label(client, label_name)
        client.add_gmail_labels(item["uid"], [label_name])
        print(f"  Labeled UID {item['uid']} -> {label_name}")


def build_ai_input(emails):
    """Build the list of subjects+bodies to send to the AI model."""
    items = []
    for i, item in enumerate(emails, start=1):
        msg = email.message_from_bytes(item["raw"], policy=policy.default)
        items.append(
            {
                "index": i,
                "sender": msg["From"] or "",
                "subject": msg["Subject"] or "",
                "body": get_body(msg)[:2000],
            }
        )
    return items


def thematic_analysis(email_items, api_key, model_name):
    """Use Google Gemini to group emails by theme; return parsed JSON."""
    if not api_key:
        sys.exit(
            "ERROR: GEMINI_API_KEY not set. Get a free key at "
            "https://aistudio.google.com/apikey"
        )
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name,
        system_instruction=(
            "You are an assistant that groups emails by overarching theme. "
            "Given a JSON array of emails (each with index, sender, subject, body), "
            "categorize them into themes. Respond with ONLY valid JSON: "
            '{"themes": [{"theme": "<name>", "description": "<short>", '
            '"emails": [{"index": <int>, "sender": "...", "subject": "..."}]}]}. '
            "Every input email must appear in exactly one theme."
        ),
    )
    user_content = json.dumps(email_items, ensure_ascii=False, indent=2)
    response = model.generate_content(
        user_content,
        generation_config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Gmail nested-domain labeling + AI themes."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=int(os.getenv("EMAIL_COUNT", DEFAULT_EMAIL_COUNT)),
        help="Number of latest Inbox emails to process (default: env EMAIL_COUNT or 10).",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        help="Gemini model for thematic analysis (default: gemini-1.5-flash).",
    )
    args = parser.parse_args()

    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    print("Connecting to Gmail IMAP...")
    client = connect_imap(gmail_user, gmail_password)
    try:
        print(f"Fetching {args.count} latest Inbox emails...")
        emails = fetch_latest_emails(client, args.count)
        if not emails:
            print("No emails found.")
            return

        print("Assigning nested domain labels...")
        label_emails(client, emails)
    finally:
        client.logout()

    print(f"Running AI thematic analysis (model: {args.model})...")
    email_items = build_ai_input(emails)
    themes = thematic_analysis(email_items, gemini_key, args.model)

    with open(THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)
    print(f"Wrote thematic analysis to {THEMES_FILE}")


if __name__ == "__main__":
    main()
