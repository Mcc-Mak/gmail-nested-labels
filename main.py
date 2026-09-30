r"""Workflow-1: Gmail flat-domain labeling + AI thematic analysis.

Uses IMAP with a Gmail App Password (no Google Cloud Console needed) and
the OpenCode built-in model `big-pickle` (no API key needed) for thematic
analysis.

Steps:
  1. Connect to Gmail via IMAP using an App Password.
  2. Fetch the N latest Inbox emails.
  3. Clear all labels except `\Inbox` from the fetched emails, then group
     them by their flat reversed-domain label (e.g. hko.gov.hk ->
     hk-gov-hko). For each group: create the label via IMAP CREATE if
     missing, apply it to every email, and remove `\Inbox` (archive).
     Operations are batched per label to minimize server round-trips, and
     the result is verified by re-fetching X-GM-LABELS. Emails with no
     extractable domain are left in the Inbox unlabeled.
  4. Send the subjects and bodies to the OpenCode model to group the
     emails by theme and write the result to themes-ai.json.
"""

import argparse
import email
from email import policy
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile

from dotenv import load_dotenv
from imapclient import IMAPClient
from imapclient.exceptions import IMAPClientError

IMAP_HOST = "imap.gmail.com"
THEMES_FILE = "themes-ai.json"
DEFAULT_EMAIL_COUNT = 10
DEFAULT_MODEL = "opencode/big-pickle"


def connect_imap(user, app_password):
    """Connect and login to Gmail IMAP; return an IMAPClient."""
    if not user or not app_password:
        sys.exit(
            "ERROR: GMAIL_USER and GMAIL_APP_PASSWORD must be set in .env.\n"
            "See README.md for how to generate an App Password."
        )
    client = IMAPClient(IMAP_HOST, ssl=True, ssl_context=ssl.create_default_context())
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
    """Reverse the domain parts and join with '-'.

    Canonical example: hko.gov.hk -> hk-gov-hko
    """
    parts = [p for p in domain.split(".") if p]
    return "-".join(reversed(parts))


def ensure_label(client, label_name):
    """Create label_name via IMAP CREATE if it does not exist.

    Gmail maps IMAP folder creation to label creation. A flat label (no '/')
    creates no parent labels. A pre-existing label (ALREADYEXISTS) is fine;
    any other error is re-raised so it is not silently hidden.
    """
    try:
        client.create_folder(label_name)
        print(f"  Created label: {label_name}")
    except IMAPClientError as exc:
        msg = str(exc).lower()
        if "alreadyexists" in msg or "already exists" in msg:
            return
        raise


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
    r"""Clear, label, and archive emails (batched and verified).

    Pipeline:
      1. Resolve each email's flat target label from its sender domain.
         Emails with no extractable domain are skipped (left in Inbox).
      2. Clear: fetch current X-GM-LABELS for all target UIDs in one call;
         for each, remove every existing label except `\Inbox`.
      3. Label + archive: group UIDs by target label. For each group, ensure
         the label exists (CREATE), add it to all UIDs, then remove
         `\Inbox` (archive) from all UIDs. Batching minimizes server
         round-trips (avoids Gmail IMAP rate-limiting).
      4. Verify: re-fetch X-GM-LABELS and report ground truth per UID. An
         email counts as archived only if `\Inbox` is actually absent.
    """
    # 1. Resolve target labels.
    targets = []
    for item in emails:
        uid = item["uid"]
        msg = email.message_from_bytes(item["raw"], policy=policy.default)
        from_header = msg["From"] or ""
        domain = extract_domain(from_header)
        if not domain:
            print(f"  UID {uid}: no domain, left in Inbox")
            continue
        targets.append((uid, domain_to_label(domain)))
    if not targets:
        return

    target_uids = [uid for uid, _ in targets]

    # 2. Clear all labels except \Inbox (one fetch, per-uid removals).
    current_map = client.get_gmail_labels(target_uids)
    for uid in target_uids:
        to_remove = [lab for lab in current_map.get(uid, ()) if lab != "\\Inbox"]
        if to_remove:
            client.remove_gmail_labels(uid, to_remove)

    # 3. Group by label; ensure, add, archive (batched per label).
    by_label = {}
    for uid, label in targets:
        by_label.setdefault(label, []).append(uid)
    for label_name, uids in by_label.items():
        print(f"  {label_name}: {len(uids)} email(s)")
        try:
            ensure_label(client, label_name)
        except IMAPClientError as exc:
            print(f"    ERROR creating label: {exc} -- skipping")
            continue
        try:
            client.add_gmail_labels(uids, [label_name])
            client.remove_gmail_labels(uids, ["\\Inbox"])
        except IMAPClientError as exc:
            print(f"    ERROR labeling/archiving: {exc}")

    # 4. Verify ground truth.
    after = client.get_gmail_labels(target_uids)
    archived = failed = 0
    for uid, label in targets:
        labels = list(after.get(uid, ()))
        has_label = label in labels
        in_inbox = "\\Inbox" in labels
        if has_label and not in_inbox:
            archived += 1
        else:
            failed += 1
            print(
                f"  UID {uid}: VERIFY FAILED "
                f"(label={label!r} present={has_label}, in_inbox={in_inbox}, "
                f"have={labels})"
            )
    print(f"  Done: {archived} archived, {failed} failed of {len(targets)} targeted.")


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


def thematic_analysis(email_items, model):
    """Use the OpenCode built-in model to group emails by theme.

    Calls `opencode run -m <model> --format json` with the email data
    attached as a file. Returns parsed JSON.
    """
    prompt = (
        "Read the attached JSON file. It contains emails with index, sender, "
        "subject, and body fields. Group them by overarching theme. "
        "Respond with ONLY valid JSON, no markdown, no explanation: "
        '{"themes": [{"theme": "<name>", "description": "<short>", '
        '"emails": [{"index": <int>, "sender": "...", "subject": "..."}]}]}. '
        "Every input email must appear in exactly one theme."
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(email_items, f, ensure_ascii=False, indent=2)
        temp_path = f.name

    try:
        result = subprocess.run(
            [
                "opencode", "run",
                "-m", model,
                "--format", "json",
                prompt,
                "-f", temp_path,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        os.unlink(temp_path)

    if result.returncode != 0:
        sys.exit(
            f"ERROR: opencode run failed (exit {result.returncode}):\n"
            f"{result.stderr}"
        )

    text_parts = []
    for line in result.stdout.strip().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            text_parts.append(event["part"]["text"])

    full_text = "".join(text_parts).strip()
    try:
        return json.loads(full_text)
    except json.JSONDecodeError:
        sys.exit(f"ERROR: could not parse AI output as JSON:\n{full_text[:500]}")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Gmail flat-domain labeling (clear, label, archive) + AI themes."
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
        default=os.getenv("OPENCODE_MODEL", DEFAULT_MODEL),
        help="OpenCode model for thematic analysis (default: opencode/big-pickle).",
    )
    args = parser.parse_args()

    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")

    print("Connecting to Gmail IMAP...")
    client = connect_imap(gmail_user, gmail_password)
    try:
        print(f"Fetching {args.count} latest Inbox emails...")
        emails = fetch_latest_emails(client, args.count)
        if not emails:
            print("No emails found.")
            return

        print("Clearing, labeling (batched), archiving, and verifying...")
        label_emails(client, emails)
    finally:
        client.logout()

    print(f"Running AI thematic analysis (model: {args.model})...")
    email_items = build_ai_input(emails)
    themes = thematic_analysis(email_items, args.model)

    with open(THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)
    print(f"Wrote thematic analysis to {THEMES_FILE}")


if __name__ == "__main__":
    main()
