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
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/tasks.readonly",
]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "tasks-token.json"


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


def tasks_service():
    return build("tasks", "v1", credentials=load_creds())


def auth():
    load_creds()
    print("Auth OK")


def list_tasklists(max_results=20):
    service = tasks_service()
    res = service.tasklists().list(maxResults=max_results).execute()
    print(json.dumps(res.get("items", []), indent=2))


def create_tasklist(title):
    service = tasks_service()
    result = service.tasklists().insert(body={"title": title}).execute()
    print(json.dumps(result, indent=2))


def list_tasks(tasklist_id, show_completed=True, max_results=50):
    service = tasks_service()
    res = service.tasks().list(tasklist=tasklist_id, showCompleted=show_completed, maxResults=max_results).execute()
    print(json.dumps(res.get("items", []), indent=2))


def create_task(tasklist_id, title, notes=None, due=None):
    service = tasks_service()
    body = {"title": title}
    if notes:
        body["notes"] = notes
    if due:
        body["due"] = due
    result = service.tasks().insert(tasklist=tasklist_id, body=body).execute()
    print(json.dumps(result, indent=2))


def get_task(tasklist_id, task_id):
    service = tasks_service()
    result = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
    print(json.dumps(result, indent=2))


def update_task(tasklist_id, task_id, title=None, notes=None, due=None, status=None):
    service = tasks_service()
    task = service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
    if title is not None:
        task["title"] = title
    if notes is not None:
        task["notes"] = notes
    if due is not None:
        task["due"] = due
    if status is not None:
        task["status"] = status
    result = service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()
    print(json.dumps(result, indent=2))


def delete_task(tasklist_id, task_id):
    service = tasks_service()
    service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
    print(json.dumps({"deleted": True, "tasklist_id": tasklist_id, "task_id": task_id}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")

    p_lists = sub.add_parser("list-tasklists")
    p_lists.add_argument("--max-results", type=int, default=20)

    p_create_list = sub.add_parser("create-tasklist")
    p_create_list.add_argument("--title", required=True)

    p_list_tasks = sub.add_parser("list-tasks")
    p_list_tasks.add_argument("--tasklist-id", required=True)
    p_list_tasks.add_argument("--show-completed", action="store_true")
    p_list_tasks.add_argument("--max-results", type=int, default=50)

    p_create_task = sub.add_parser("create-task")
    p_create_task.add_argument("--tasklist-id", required=True)
    p_create_task.add_argument("--title", required=True)
    p_create_task.add_argument("--notes")
    p_create_task.add_argument("--due")

    p_get = sub.add_parser("get-task")
    p_get.add_argument("--tasklist-id", required=True)
    p_get.add_argument("--task-id", required=True)

    p_update = sub.add_parser("update-task")
    p_update.add_argument("--tasklist-id", required=True)
    p_update.add_argument("--task-id", required=True)
    p_update.add_argument("--title")
    p_update.add_argument("--notes")
    p_update.add_argument("--due")
    p_update.add_argument("--status")

    p_delete = sub.add_parser("delete-task")
    p_delete.add_argument("--tasklist-id", required=True)
    p_delete.add_argument("--task-id", required=True)

    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "list-tasklists":
        list_tasklists(args.max_results)
    elif args.cmd == "create-tasklist":
        create_tasklist(args.title)
    elif args.cmd == "list-tasks":
        list_tasks(args.tasklist_id, args.show_completed, args.max_results)
    elif args.cmd == "create-task":
        create_task(args.tasklist_id, args.title, args.notes, args.due)
    elif args.cmd == "get-task":
        get_task(args.tasklist_id, args.task_id)
    elif args.cmd == "update-task":
        update_task(args.tasklist_id, args.task_id, args.title, args.notes, args.due, args.status)
    elif args.cmd == "delete-task":
        delete_task(args.tasklist_id, args.task_id)


if __name__ == "__main__":
    main()
