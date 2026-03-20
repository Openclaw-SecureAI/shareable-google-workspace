#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/forms.responses.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly",
]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "forms-token.json"


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


def forms_service():
    return build("forms", "v1", credentials=load_creds())


def drive_service():
    return build("drive", "v3", credentials=load_creds())


def auth():
    load_creds()
    print("Auth OK")


def list_forms(page_size=20):
    service = drive_service()
    res = service.files().list(
        q="mimeType='application/vnd.google-apps.form' and trashed=false",
        pageSize=page_size,
        fields="files(id,name,createdTime,modifiedTime,webViewLink,owners)",
        orderBy="modifiedTime desc",
    ).execute()
    print(json.dumps(res.get("files", []), indent=2))


def create_form(title, document_title=None):
    service = forms_service()
    body = {"info": {"title": title}}
    if document_title:
        body["info"]["documentTitle"] = document_title
    result = service.forms().create(body=body).execute()
    print(json.dumps(result, indent=2))


def get_form(form_id):
    service = forms_service()
    result = service.forms().get(formId=form_id).execute()
    print(json.dumps(result, indent=2))


def update_form_info(form_id, title=None, document_title=None, description=None):
    service = forms_service()
    requests = []
    info = {}
    update_mask = []
    if title is not None:
        info["title"] = title
        update_mask.append("title")
    if document_title is not None:
        info["documentTitle"] = document_title
        update_mask.append("document_title")
    if description is not None:
        info["description"] = description
        update_mask.append("description")
    if not update_mask:
        raise SystemExit("Provide at least one field to update")
    requests.append(
        {
            "updateFormInfo": {
                "info": info,
                "updateMask": ",".join(update_mask),
            }
        }
    )
    result = service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
    verified = service.forms().get(formId=form_id).execute()
    print(json.dumps({"batchUpdate": result, "verified_form": verified}, indent=2))


def add_text_question(form_id, title, index=0, description=None, required=False, paragraph=False):
    service = forms_service()
    item = {
        "title": title,
        "questionItem": {
            "question": {
                "required": required,
                "textQuestion": {"paragraph": paragraph},
            }
        },
    }
    if description:
        item["description"] = description
    result = service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": [
                {
                    "createItem": {
                        "item": item,
                        "location": {"index": index},
                    }
                }
            ]
        },
    ).execute()
    verified = service.forms().get(formId=form_id).execute()
    print(json.dumps({"batchUpdate": result, "verified_form": verified}, indent=2))


def add_choice_question(form_id, title, options, index=0, description=None, required=False, question_type="RADIO"):
    service = forms_service()
    normalized_options = [{"value": value} for value in options]
    item = {
        "title": title,
        "questionItem": {
            "question": {
                "required": required,
                "choiceQuestion": {
                    "type": question_type,
                    "options": normalized_options,
                    "shuffle": False,
                },
            }
        },
    }
    if description:
        item["description"] = description
    result = service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": [
                {
                    "createItem": {
                        "item": item,
                        "location": {"index": index},
                    }
                }
            ]
        },
    ).execute()
    verified = service.forms().get(formId=form_id).execute()
    print(json.dumps({"batchUpdate": result, "verified_form": verified}, indent=2))


def list_responses(form_id):
    service = forms_service()
    result = service.forms().responses().list(formId=form_id).execute()
    print(json.dumps(result.get("responses", []), indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")

    p_list = sub.add_parser("list-forms")
    p_list.add_argument("--page-size", type=int, default=20)

    p_create = sub.add_parser("create-form")
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--document-title")

    p_get = sub.add_parser("get-form")
    p_get.add_argument("--form-id", required=True)

    p_update = sub.add_parser("update-form-info")
    p_update.add_argument("--form-id", required=True)
    p_update.add_argument("--title")
    p_update.add_argument("--document-title")
    p_update.add_argument("--description")

    p_text = sub.add_parser("add-text-question")
    p_text.add_argument("--form-id", required=True)
    p_text.add_argument("--title", required=True)
    p_text.add_argument("--index", type=int, default=0)
    p_text.add_argument("--description")
    p_text.add_argument("--required", action="store_true")
    p_text.add_argument("--paragraph", action="store_true")

    p_choice = sub.add_parser("add-choice-question")
    p_choice.add_argument("--form-id", required=True)
    p_choice.add_argument("--title", required=True)
    p_choice.add_argument("--option", dest="options", action="append", required=True)
    p_choice.add_argument("--index", type=int, default=0)
    p_choice.add_argument("--description")
    p_choice.add_argument("--required", action="store_true")
    p_choice.add_argument("--question-type", choices=["RADIO", "CHECKBOX", "DROP_DOWN"], default="RADIO")

    p_responses = sub.add_parser("list-responses")
    p_responses.add_argument("--form-id", required=True)

    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "list-forms":
        list_forms(args.page_size)
    elif args.cmd == "create-form":
        create_form(args.title, args.document_title)
    elif args.cmd == "get-form":
        get_form(args.form_id)
    elif args.cmd == "update-form-info":
        update_form_info(args.form_id, args.title, args.document_title, args.description)
    elif args.cmd == "add-text-question":
        add_text_question(args.form_id, args.title, args.index, args.description, args.required, args.paragraph)
    elif args.cmd == "add-choice-question":
        add_choice_question(args.form_id, args.title, args.options, args.index, args.description, args.required, args.question_type)
    elif args.cmd == "list-responses":
        list_responses(args.form_id)


if __name__ == "__main__":
    main()
