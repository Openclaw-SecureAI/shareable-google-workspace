#!/usr/bin/env python3
import argparse
import base64
import json
import os
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "gmail-token.json"


def manual_auth():
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_FILE), SCOPES)
    flow.redirect_uri = "http://localhost"
    auth_url, _ = flow.authorization_url(prompt="consent")
    print("Open this URL in your browser:\n")
    print(auth_url)
    print("\nAfter approving access, paste the FULL redirect URL here:")
    redirect_response = input().strip()
    flow.fetch_token(authorization_response=redirect_response)
    TOKEN_FILE.write_text(flow.credentials.to_json())
    print(f"Saved token to {TOKEN_FILE}")
    return flow.credentials


def load_creds():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = manual_auth()
        TOKEN_FILE.write_text(creds.to_json())
    return creds


def gmail_service():
    return build("gmail", "v1", credentials=load_creds())


def auth():
    load_creds()
    print("Auth OK")


def list_messages(query=None, max_results=10):
    service = gmail_service()
    kwargs = {"userId": "me", "maxResults": max_results}
    if query:
        kwargs["q"] = query
    res = service.users().messages().list(**kwargs).execute()
    msgs = []
    for item in res.get("messages", []):
        msg = service.users().messages().get(userId="me", id=item["id"], format="metadata", metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        msgs.append({
            "id": msg.get("id"),
            "threadId": msg.get("threadId"),
            "from": headers.get("From"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "labelIds": msg.get("labelIds", []),
        })
    print(json.dumps(msgs, indent=2))


def get_message(message_id):
    service = gmail_service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    body_text = ""

    def walk(part):
        nonlocal body_text
        mime = part.get("mimeType")
        data = (part.get("body") or {}).get("data")
        if mime == "text/plain" and data:
            body_text += base64.urlsafe_b64decode(data.encode()).decode(errors="replace")
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(msg.get("payload", {}))
    print(json.dumps({
        "id": msg.get("id"),
        "threadId": msg.get("threadId"),
        "labelIds": msg.get("labelIds", []),
        "headers": headers,
        "text": body_text,
    }, indent=2))


def draft_message(to, subject, body_text):
    service = gmail_service()
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body_text)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    print(json.dumps(draft, indent=2))


def send_message(to, subject, body_text):
    service = gmail_service()
    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body_text)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(json.dumps(sent, indent=2))


def modify_labels(message_id, add_labels=None, remove_labels=None):
    service = gmail_service()
    body = {"addLabelIds": add_labels or [], "removeLabelIds": remove_labels or []}
    result = service.users().messages().modify(userId="me", id=message_id, body=body).execute()
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")

    p_list = sub.add_parser("list-messages")
    p_list.add_argument("--query")
    p_list.add_argument("--max-results", type=int, default=10)

    p_get = sub.add_parser("get-message")
    p_get.add_argument("--message-id", required=True)

    p_draft = sub.add_parser("draft-message")
    p_draft.add_argument("--to", required=True)
    p_draft.add_argument("--subject", required=True)
    p_draft.add_argument("--body", required=True)

    p_send = sub.add_parser("send-message")
    p_send.add_argument("--to", required=True)
    p_send.add_argument("--subject", required=True)
    p_send.add_argument("--body", required=True)

    p_mod = sub.add_parser("modify-labels")
    p_mod.add_argument("--message-id", required=True)
    p_mod.add_argument("--add-label", action="append")
    p_mod.add_argument("--remove-label", action="append")

    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "list-messages":
        list_messages(args.query, args.max_results)
    elif args.cmd == "get-message":
        get_message(args.message_id)
    elif args.cmd == "draft-message":
        draft_message(args.to, args.subject, args.body)
    elif args.cmd == "send-message":
        send_message(args.to, args.subject, args.body)
    elif args.cmd == "modify-labels":
        modify_labels(args.message_id, args.add_label, args.remove_label)


if __name__ == "__main__":
    main()
