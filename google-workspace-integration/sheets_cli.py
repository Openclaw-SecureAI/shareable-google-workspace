#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "sheets-token.json"


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


def sheets_service():
    return build("sheets", "v4", credentials=load_creds())


def auth():
    load_creds()
    print("Auth OK")


def create_sheet(title):
    service = sheets_service()
    body = {"properties": {"title": title}}
    sheet = service.spreadsheets().create(body=body).execute()
    print(json.dumps({
        "spreadsheetId": sheet.get("spreadsheetId"),
        "spreadsheetUrl": sheet.get("spreadsheetUrl"),
        "title": sheet.get("properties", {}).get("title"),
    }, indent=2))


def metadata(spreadsheet_id):
    service = sheets_service()
    result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    print(json.dumps({
        "spreadsheetId": result.get("spreadsheetId"),
        "title": result.get("properties", {}).get("title"),
        "sheets": [
            {
                "sheetId": s.get("properties", {}).get("sheetId"),
                "title": s.get("properties", {}).get("title"),
            }
            for s in result.get("sheets", [])
        ],
    }, indent=2))


def get_range(spreadsheet_id, rng):
    service = sheets_service()
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=rng).execute()
    print(json.dumps({
        "range": result.get("range"),
        "values": result.get("values", []),
    }, indent=2))


def update_range(spreadsheet_id, rng, values_json, input_option):
    service = sheets_service()
    values = json.loads(values_json)
    body = {"values": values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=rng,
        valueInputOption=input_option,
        body=body,
    ).execute()
    print(json.dumps(result, indent=2))


def append_rows(spreadsheet_id, rng, values_json, input_option):
    service = sheets_service()
    values = json.loads(values_json)
    body = {"values": values}
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=rng,
        valueInputOption=input_option,
        insertDataOption="INSERT_ROWS",
        body=body,
    ).execute()
    print(json.dumps(result, indent=2))


def clear_range(spreadsheet_id, rng):
    service = sheets_service()
    result = service.spreadsheets().values().clear(spreadsheetId=spreadsheet_id, range=rng, body={}).execute()
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    p_create = sub.add_parser("create-sheet")
    p_create.add_argument("--title", required=True)
    p_meta = sub.add_parser("metadata")
    p_meta.add_argument("--sheet-id", required=True)
    p_get = sub.add_parser("get-range")
    p_get.add_argument("--sheet-id", required=True)
    p_get.add_argument("--range", required=True)
    p_update = sub.add_parser("update-range")
    p_update.add_argument("--sheet-id", required=True)
    p_update.add_argument("--range", required=True)
    p_update.add_argument("--values-json", required=True)
    p_update.add_argument("--input-option", default="USER_ENTERED")
    p_append = sub.add_parser("append-rows")
    p_append.add_argument("--sheet-id", required=True)
    p_append.add_argument("--range", required=True)
    p_append.add_argument("--values-json", required=True)
    p_append.add_argument("--input-option", default="USER_ENTERED")
    p_clear = sub.add_parser("clear-range")
    p_clear.add_argument("--sheet-id", required=True)
    p_clear.add_argument("--range", required=True)
    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "create-sheet":
        create_sheet(args.title)
    elif args.cmd == "metadata":
        metadata(args.sheet_id)
    elif args.cmd == "get-range":
        get_range(args.sheet_id, args.range)
    elif args.cmd == "update-range":
        update_range(args.sheet_id, args.range, args.values_json, args.input_option)
    elif args.cmd == "append-rows":
        append_rows(args.sheet_id, args.range, args.values_json, args.input_option)
    elif args.cmd == "clear-range":
        clear_range(args.sheet_id, args.range)


if __name__ == "__main__":
    main()
