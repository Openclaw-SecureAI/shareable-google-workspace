#!/usr/bin/env python3
import argparse
import json
import mimetypes
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "docs-drive-token.json"


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


def drive_service():
    return build("drive", "v3", credentials=load_creds())


def docs_service():
    return build("docs", "v1", credentials=load_creds())


def auth():
    load_creds()
    print("Auth OK")


def create_doc(title):
    service = docs_service()
    doc = service.documents().create(body={"title": title}).execute()
    print(json.dumps({
        "documentId": doc.get("documentId"),
        "title": doc.get("title"),
    }, indent=2))


def write_doc(doc_id, text, append=False):
    service = docs_service()
    doc = service.documents().get(documentId=doc_id).execute()
    end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1)
    insert_index = max(1, end_index - 1)
    if not append:
        requests = [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": insert_index}}}] if insert_index > 1 else []
        requests.append({"insertText": {"location": {"index": 1}, "text": text}})
    else:
        requests = [{"insertText": {"location": {"index": insert_index}, "text": text}}]
    service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    print(json.dumps({"documentId": doc_id, "written": True, "append": append}, indent=2))


def get_doc(doc_id):
    service = docs_service()
    doc = service.documents().get(documentId=doc_id).execute()
    text_parts = []
    for elem in doc.get("body", {}).get("content", []):
        para = elem.get("paragraph")
        if not para:
            continue
        for pe in para.get("elements", []):
            tr = pe.get("textRun")
            if tr:
                text_parts.append(tr.get("content", ""))
    print(json.dumps({
        "documentId": doc.get("documentId"),
        "title": doc.get("title"),
        "text": "".join(text_parts),
    }, indent=2))


def search_drive(query, max_results=10):
    service = drive_service()
    q = query.replace("'", "\\'")
    res = service.files().list(
        q=f"name contains '{q}' and trashed = false",
        pageSize=max_results,
        fields="files(id,name,mimeType,parents,webViewLink)",
    ).execute()
    print(json.dumps(res.get("files", []), indent=2))


def list_folder(folder_id='root', max_results=100):
    service = drive_service()
    res = service.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        pageSize=max_results,
        fields="files(id,name,mimeType,parents,webViewLink)",
        orderBy="folder,name",
    ).execute()
    print(json.dumps(res.get("files", []), indent=2))


def create_folder(name, parent_id=None):
    service = drive_service()
    body = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        body["parents"] = [parent_id]
    folder = service.files().create(body=body, fields="id,name,mimeType,parents,webViewLink").execute()
    print(json.dumps(folder, indent=2))


def get_file(file_id):
    service = drive_service()
    meta = service.files().get(fileId=file_id, fields="id,name,mimeType,parents,webViewLink,createdTime,modifiedTime,owners,permissions").execute()
    print(json.dumps(meta, indent=2))


def upload_file(local_path, name=None, parent_id=None, mime_type=None):
    service = drive_service()
    p = Path(local_path)
    if not p.exists():
        raise SystemExit(f"Local file not found: {local_path}")
    mt = mime_type or mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    body = {"name": name or p.name}
    if parent_id:
        body["parents"] = [parent_id]
    media = MediaFileUpload(str(p), mimetype=mt, resumable=False)
    result = service.files().create(body=body, media_body=media, fields="id,name,mimeType,parents,webViewLink").execute()
    print(json.dumps(result, indent=2))


def move_file(file_id, add_parent_id=None, remove_parent_id=None):
    service = drive_service()
    current = service.files().get(fileId=file_id, fields="id,parents,name").execute()
    existing_parents = current.get("parents", [])
    if remove_parent_id is None:
        remove_parent_id = ",".join(existing_parents) if existing_parents else None
    updated = service.files().update(
        fileId=file_id,
        addParents=add_parent_id,
        removeParents=remove_parent_id,
        fields="id,name,parents,webViewLink",
    ).execute()
    print(json.dumps(updated, indent=2))


def copy_file(file_id, name=None, parent_id=None):
    service = drive_service()
    body = {}
    if name:
        body["name"] = name
    if parent_id:
        body["parents"] = [parent_id]
    copied = service.files().copy(fileId=file_id, body=body, fields="id,name,mimeType,parents,webViewLink").execute()
    print(json.dumps(copied, indent=2))


def export_google_doc(file_id, output_path, mime_type="application/pdf"):
    service = drive_service()
    fh = io.FileIO(output_path, "wb")
    request_ = service.files().export_media(fileId=file_id, mimeType=mime_type)
    downloader = MediaIoBaseDownload(fh, request_)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    print(json.dumps({"exported": True, "file_id": file_id, "output_path": output_path, "mime_type": mime_type}, indent=2))


def download_file(file_id, output_path):
    service = drive_service()
    fh = io.FileIO(output_path, "wb")
    request_ = service.files().get_media(fileId=file_id)
    downloader = MediaIoBaseDownload(fh, request_)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.close()
    print(json.dumps({"downloaded": True, "file_id": file_id, "output_path": output_path}, indent=2))


def set_permission(file_id, email=None, role="reader", perm_type="user", anyone=False):
    service = drive_service()
    body = {"role": role}
    if anyone:
        body["type"] = "anyone"
    else:
        if not email:
            raise SystemExit("email is required unless --anyone is used")
        body["type"] = perm_type
        body["emailAddress"] = email
    perm = service.permissions().create(fileId=file_id, body=body, fields="id,type,role,emailAddress").execute()
    print(json.dumps(perm, indent=2))


def share_file(file_id, email=None, role="reader", anyone=False):
    set_permission(file_id=file_id, email=email, role=role, anyone=anyone)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth")

    p_create = sub.add_parser("create-doc")
    p_create.add_argument("--title", required=True)

    p_write = sub.add_parser("write-doc")
    p_write.add_argument("--doc-id", required=True)
    p_write.add_argument("--text", required=True)
    p_write.add_argument("--append", action="store_true")

    p_get = sub.add_parser("get-doc")
    p_get.add_argument("--doc-id", required=True)

    p_search = sub.add_parser("search-drive")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--max-results", type=int, default=10)

    p_list = sub.add_parser("list-folder")
    p_list.add_argument("--folder-id", default="root")
    p_list.add_argument("--max-results", type=int, default=100)

    p_folder = sub.add_parser("create-folder")
    p_folder.add_argument("--name", required=True)
    p_folder.add_argument("--parent-id")

    p_file = sub.add_parser("get-file")
    p_file.add_argument("--file-id", required=True)

    p_upload = sub.add_parser("upload-file")
    p_upload.add_argument("--local-path", required=True)
    p_upload.add_argument("--name")
    p_upload.add_argument("--parent-id")
    p_upload.add_argument("--mime-type")

    p_move = sub.add_parser("move-file")
    p_move.add_argument("--file-id", required=True)
    p_move.add_argument("--add-parent-id")
    p_move.add_argument("--remove-parent-id")

    p_copy = sub.add_parser("copy-file")
    p_copy.add_argument("--file-id", required=True)
    p_copy.add_argument("--name")
    p_copy.add_argument("--parent-id")

    p_export = sub.add_parser("export-google-doc")
    p_export.add_argument("--file-id", required=True)
    p_export.add_argument("--output-path", required=True)
    p_export.add_argument("--mime-type", default="application/pdf")

    p_download = sub.add_parser("download-file")
    p_download.add_argument("--file-id", required=True)
    p_download.add_argument("--output-path", required=True)

    p_perm = sub.add_parser("set-permission")
    p_perm.add_argument("--file-id", required=True)
    p_perm.add_argument("--email")
    p_perm.add_argument("--role", default="reader")
    p_perm.add_argument("--type", dest="perm_type", default="user")
    p_perm.add_argument("--anyone", action="store_true")

    p_share = sub.add_parser("share-file")
    p_share.add_argument("--file-id", required=True)
    p_share.add_argument("--email")
    p_share.add_argument("--role", default="reader")
    p_share.add_argument("--anyone", action="store_true")

    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "create-doc":
        create_doc(args.title)
    elif args.cmd == "write-doc":
        write_doc(args.doc_id, args.text, args.append)
    elif args.cmd == "get-doc":
        get_doc(args.doc_id)
    elif args.cmd == "search-drive":
        search_drive(args.query, args.max_results)
    elif args.cmd == "list-folder":
        list_folder(args.folder_id, args.max_results)
    elif args.cmd == "create-folder":
        create_folder(args.name, args.parent_id)
    elif args.cmd == "get-file":
        get_file(args.file_id)
    elif args.cmd == "upload-file":
        upload_file(args.local_path, args.name, args.parent_id, args.mime_type)
    elif args.cmd == "move-file":
        move_file(args.file_id, args.add_parent_id, args.remove_parent_id)
    elif args.cmd == "copy-file":
        copy_file(args.file_id, args.name, args.parent_id)
    elif args.cmd == "export-google-doc":
        export_google_doc(args.file_id, args.output_path, args.mime_type)
    elif args.cmd == "download-file":
        download_file(args.file_id, args.output_path)
    elif args.cmd == "set-permission":
        set_permission(args.file_id, args.email, args.role, args.perm_type, args.anyone)
    elif args.cmd == "share-file":
        share_file(args.file_id, args.email, args.role, args.anyone)


if __name__ == "__main__":
    main()
