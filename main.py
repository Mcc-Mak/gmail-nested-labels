r"""Workflow-1：Gmail 扁平網域標記 + AI 主題分析。

以 IMAP 搭配 Gmail 應用程式密碼連線（免 Google Cloud Console），並
使用 OpenCode 內建模型 `big-pickle` 進行主題分析（免 API 金鑰）。

步驟：
  1. 以應用程式密碼透過 IMAP 連線 Gmail。
  2. 擷取最新 N 封收件匣郵件。
  3. 清除擷取郵件中 `\Inbox` 以外的所有標籤，再依扁平反轉網域標籤
     分組（例如 hko.gov.hk -> hk-gov-hko）。每組：若標籤不存在則以
     IMAP CREATE 建立，套用至每封郵件，再移除 `\Inbox`（封存）。
     操作以標籤為單位批次執行以減少伺服器往返次數，並以重新擷取
     X-GM-LABELS 驗證結果。無法擷取網域的郵件留在收件匣不標記。
     加上 `--no-archive` 可跳過封存步驟（除錯模式）。
  4. 將主旨與內文傳給 OpenCode 模型，依主題分組並寫入 themes-ai.json。
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
    """連線並登入 Gmail IMAP；回傳 IMAPClient。"""
    if not user or not app_password:
        sys.exit(
            "錯誤：GMAIL_USER 和 GMAIL_APP_PASSWORD 必須在 .env 中設定。\n"
            "請參閱 README.md 了解如何產生應用程式密碼。"
        )
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = True
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    client = IMAPClient(IMAP_HOST, ssl=True, ssl_context=ssl_context)
    client.login(user, app_password)
    return client


def fetch_latest_emails(client, n):
    """擷取最新 N 封收件匣郵件完整內容（RFC822）。

    回傳 dict 列表：{"uid": int, "raw": bytes}。
    UID 單調遞增，故最後 N 封即為最新郵件。
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
    """從 From 標頭擷取小寫寄件者網域。

    處理 "Name <user@example.com>" 及單純 "user@example.com" 兩種格式。
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
    """反轉網域各部分並以 '-' 接合。

    標準範例：hko.gov.hk -> hk-gov-hko
    """
    parts = [p for p in domain.split(".") if p]
    return "-".join(reversed(parts))


def ensure_label(client, label_name):
    """以 IMAP CREATE 建立標籤（若不存在）。

    Gmail 將 '-' 和 '/' 視為等價——當 '/' 格式標籤已存在時，
    CREATE "com-github" 會傳回 ALREADYEXISTS 並對應至既有的
    "com/github"。此函式在偵測到此衝突時，刪除舊的 '/' 格式標籤
    後重試建立 '-' 格式標籤，確保遵守 SPEC 的扁平標籤規則。
    """
    try:
        client.create_folder(label_name)
        print(f"  🏷️ 已建立標籤：{label_name}")
        return
    except IMAPClientError as exc:
        msg = str(exc).lower()
        if "alreadyexists" not in msg and "already exists" not in msg:
            raise

    # ALREADYEXISTS：嘗試刪除舊 '/' 格式標籤後重試。
    slash_name = label_name.replace("-", "/")
    try:
        client.delete_folder(slash_name)
        print(f"  🗑️ 已刪除舊 '/' 格式標籤：{slash_name}")
    except IMAPClientError as exc:
        if "nonexistent" in str(exc).lower() or "unknown" in str(exc).lower():
            return
        raise

    client.create_folder(label_name)
    print(f"  已建立標籤：{label_name}")


def get_body(msg):
    """從 email.message.Message 擷取純文字內文。"""
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


def _resolve_targets(emails):
    """從郵件清單解析 (uid, label) 目標清單。

    無法擷取網域的郵件跳過（留在收件匣）。
    """
    targets = []
    for item in emails:
        uid = item["uid"]
        msg = email.message_from_bytes(item["raw"], policy=policy.default)
        from_header = msg["From"] or ""
        domain = extract_domain(from_header)
        if not domain:
            print(f"  ⚠️ UID {uid}：無法擷取網域，留在收件匣")
            continue
        targets.append((uid, domain_to_label(domain)))
    return targets


def _clear_labels(client, target_uids):
    """清除每封郵件 \\Inbox 以外的所有標籤（一次擷取，逐 UID 移除）。"""
    current_map = client.get_gmail_labels(target_uids)
    for uid in target_uids:
        to_remove = [lab for lab in current_map.get(uid, ()) if lab != "\\Inbox"]
        if to_remove:
            client.remove_gmail_labels(uid, to_remove)


def _apply_labels(client, targets):
    """依標籤分組建立並套用標籤；回傳成功套用的 UID 清單。"""
    by_label = {}
    for uid, label in targets:
        by_label.setdefault(label, []).append(uid)
    labeled_uids = []
    for label_name, uids in by_label.items():
        print(f"  📧 {label_name}：{len(uids)} 封郵件")
        try:
            ensure_label(client, label_name)
        except IMAPClientError as exc:
            print(f"    ❌ 建立標籤錯誤：{exc}——跳過")
            continue
        try:
            client.add_gmail_labels(uids, [label_name])
            labeled_uids.extend(uids)
        except IMAPClientError as exc:
            print(f"    ❌ 標記錯誤：{exc}")
    return labeled_uids


def _verify_labels(client, targets):
    """驗證標籤已套用；回傳 {uid: bool}。"""
    after = client.get_gmail_labels([uid for uid, _ in targets])
    return {uid: label in list(after.get(uid, ())) for uid, label in targets}


def _archive_emails(client, labeled_uids):
    """以 STORE \\Deleted + EXPUNGE 封存（從 INBOX 移除即等同 Gmail 封存）。"""
    try:
        client.add_flags(labeled_uids, ["\\Deleted"])
        client.expunge(labeled_uids)
    except IMAPClientError as exc:
        print(f"    ❌ 封存錯誤：{exc}")


def _verify_and_report(targets, label_ok, archive, remaining_inbox=None):
    """驗證最終狀態並回報結果。"""
    ok = failed = 0
    for uid, label in targets:
        has_label = label_ok.get(uid, False)
        if archive:
            in_inbox = uid in remaining_inbox
            success = has_label and not in_inbox
        else:
            in_inbox = True
            success = has_label
        if success:
            ok += 1
        else:
            failed += 1
            print(
                f"  ❌ UID {uid}：驗證失敗 "
                f"（標籤={label!r} 已套用={has_label} 在收件匣={in_inbox}）"
            )
    action = "📦 已封存" if archive else "✅ 已標記"
    print(f"  {action}：{ok} 封成功，{failed} 封失敗，共 {len(targets)} 封目標。")


def label_emails(client, emails, archive=True):
    r"""清除、標記、封存郵件（批次處理並驗證）。

    流程：
      1. 從寄件者網域解析每封郵件的扁平目標標籤。
         無法擷取網域的郵件跳過（留在收件匣）。
      2. 清除：以一次呼叫擷取所有目標 UID 的現有 X-GM-LABELS；
         對每封郵件移除 `\Inbox` 以外的所有現有標籤。
      3. 標記：依目標標籤分組 UID。每組：確保標籤存在（CREATE），
         套用至所有 UID。批次處理可減少伺服器往返次數。
      4. 驗證標籤：從 INBOX 重新擷取 X-GM-LABELS，確認標籤已套用。
      5. 封存：在 INBOX 中以 `STORE +FLAGS \Deleted` 標記後 `EXPUNGE`。
         Gmail 的 `X-GM-LABELS` 在 INBOX 中不回報 `\Inbox`，且
         `STORE -FLAGS \Inbox` 會被 Gmail 拒絕；`STORE \Deleted` +
         `EXPUNGE` 是從 INBOX 移除郵件（等同 Gmail 封存）的標準方法，
         且使用者標籤會保留在「全部郵件」中。若 archive=False 則跳過。
      6. 驗證封存：封存後重新搜尋 INBOX，確認 UID 已不在收件匣。
    """
    targets = _resolve_targets(emails)
    if not targets:
        return

    target_uids = [uid for uid, _ in targets]

    _clear_labels(client, target_uids)
    labeled_uids = _apply_labels(client, targets)
    label_ok = _verify_labels(client, targets)

    remaining_inbox = None
    if archive and labeled_uids:
        _archive_emails(client, labeled_uids)
        remaining_inbox = set(client.search("ALL"))

    _verify_and_report(targets, label_ok, archive, remaining_inbox)


def build_ai_input(emails):
    """建構要傳給 AI 模型的主旨+內文清單。"""
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
    """使用 OpenCode 內建模型將郵件依主題分組。

    呼叫 `opencode run -m <model> --format json`，郵件資料以檔案附加。
    回傳解析後的 JSON。
    """
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", model):
        sys.exit(
            f"錯誤：無效的模型名稱 {model!r}——僅允許英數字、點、連字號、"
            f"底線、斜線。"
        )
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
            f"錯誤：opencode run 失敗（退出碼 {result.returncode}）：\n"
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
        sys.exit(f"錯誤：無法將 AI 輸出解析為 JSON：\n{full_text[:500]}")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Gmail 扁平網域標記（清除、標記、封存）+ AI 主題分析。"
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=int(os.getenv("EMAIL_COUNT", DEFAULT_EMAIL_COUNT)),
        help="處理最新幾封收件匣郵件（預設：環境變數 EMAIL_COUNT 或 10）。",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENCODE_MODEL", DEFAULT_MODEL),
        help="OpenCode 主題分析模型（預設：opencode/big-pickle）。",
    )
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="除錯模式：僅清除並標記，不封存（郵件留在收件匣以便檢驗）。",
    )
    args = parser.parse_args()

    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD", "")

    print("🔌 連線 Gmail IMAP...")
    client = connect_imap(gmail_user, gmail_password)
    try:
        print(f"📥 擷取最新 {args.count} 封收件匣郵件...")
        emails = fetch_latest_emails(client, args.count)
        if not emails:
            print("📭 找不到郵件。")
            return

        if args.no_archive:
            print("🔧 清除、標記（批次）、驗證（除錯模式：不封存）...")
        else:
            print("🔄 清除、標記（批次）、封存、驗證...")
        label_emails(client, emails, archive=not args.no_archive)
    finally:
        client.logout()

    print(f"🤖 執行 AI 主題分析（模型：{args.model}）...")
    email_items = build_ai_input(emails)
    themes = thematic_analysis(email_items, args.model)

    with open(THEMES_FILE, "w", encoding="utf-8") as f:
        json.dump(themes, f, ensure_ascii=False, indent=2)
    print(f"💾 主題分析已寫入 {THEMES_FILE}")


if __name__ == "__main__":
    main()
