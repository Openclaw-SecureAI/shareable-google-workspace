#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "calendar-token.json"
APP_CONFIG_FILE = CONFIG_DIR / "calendar-config.json"
DEFAULT_CALENDAR_NAME = "OpenClaw-Calendar"


def load_app_config():
    if APP_CONFIG_FILE.exists():
        return json.loads(APP_CONFIG_FILE.read_text())
    return {}


def save_app_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    APP_CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n")


def get_default_calendar_id():
    return load_app_config().get("default_calendar_id")


def set_default_calendar(calendar_id, calendar_name=None):
    cfg = load_app_config()
    cfg["default_calendar_id"] = calendar_id
    if calendar_name:
        cfg["default_calendar_name"] = calendar_name
    save_app_config(cfg)
    print(json.dumps(cfg, indent=2))


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


def load_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = manual_auth()
        TOKEN_FILE.write_text(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def resolve_calendar_id(service, calendar_id=None, calendar_name=None):
    if calendar_id:
        return calendar_id
    if calendar_name:
        found = find_calendar_id(service, calendar_name)
        if found:
            return found
    default_id = get_default_calendar_id()
    if default_id:
        return default_id
    raise SystemExit("No calendar specified and no default calendar configured.")


def list_calendars(service):
    res = service.calendarList().list().execute()
    for item in res.get("items", []):
        primary = " [primary]" if item.get("primary") else ""
        print(f"{item.get('summary')}\t{item.get('id')}{primary}")


def find_calendar_id(service, name):
    res = service.calendarList().list().execute()
    for item in res.get("items", []):
        if item.get("summary") == name:
            return item.get("id")
    return None


def create_calendar(service, name, make_default=False):
    body = {"summary": name}
    created = service.calendars().insert(body=body).execute()
    payload = {"summary": created.get("summary"), "id": created.get("id")}
    print(json.dumps(payload, indent=2))
    if make_default:
        set_default_calendar(created.get("id"), created.get("summary"))


def list_events(service, calendar_id, max_results):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    events = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    for event in events.get("items", []):
        start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        print(f"{start}\t{event.get('id')}\t{event.get('summary')}")


def create_event(service, calendar_id, summary, start, end=None, all_day=False, description=None, location=None):
    body = {"summary": summary}
    if description:
        body["description"] = description
    if location:
        body["location"] = location

    if all_day:
        start_date = dt.date.fromisoformat(start)
        if end:
            end_date = dt.date.fromisoformat(end)
        else:
            end_date = start_date + dt.timedelta(days=1)
        body["start"] = {"date": start_date.isoformat()}
        body["end"] = {"date": end_date.isoformat()}
    else:
        if not end:
            raise SystemExit("Timed events require --end")
        body["start"] = {"dateTime": start}
        body["end"] = {"dateTime": end}

    event = service.events().insert(calendarId=calendar_id, body=body).execute()
    print(json.dumps({
        "id": event.get("id"),
        "htmlLink": event.get("htmlLink"),
        "summary": event.get("summary"),
        "start": event.get("start"),
        "end": event.get("end"),
    }, indent=2))


def create_test_event(service, calendar_id, summary):
    start = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)
    end = start + dt.timedelta(minutes=30)
    create_event(service, calendar_id, summary, start.isoformat(), end.isoformat())


def make_event_all_day(service, calendar_id, event_id, day=None):
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    if day:
        start_date = dt.date.fromisoformat(day)
    else:
        start_raw = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
        if "T" in start_raw:
            start_date = dt.datetime.fromisoformat(start_raw.replace("Z", "+00:00")).date()
        else:
            start_date = dt.date.fromisoformat(start_raw)
    end_date = start_date + dt.timedelta(days=1)
    event["start"] = {"date": start_date.isoformat()}
    event["end"] = {"date": end_date.isoformat()}
    event.pop("recurrence", None)
    updated = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    print(json.dumps({"id": updated.get("id"), "summary": updated.get("summary"), "start": updated.get("start"), "end": updated.get("end")}, indent=2))


def update_event(service, calendar_id, event_id, summary=None, start=None, end=None, all_day=False, description=None, location=None):
    event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    if summary is not None:
        event["summary"] = summary
    if description is not None:
        event["description"] = description
    if location is not None:
        event["location"] = location
    if start is not None:
        if all_day:
            start_date = dt.date.fromisoformat(start)
            end_date = dt.date.fromisoformat(end) if end else start_date + dt.timedelta(days=1)
            event["start"] = {"date": start_date.isoformat()}
            event["end"] = {"date": end_date.isoformat()}
        else:
            if not end:
                raise SystemExit("Timed event updates require --end when changing --start")
            event["start"] = {"dateTime": start}
            event["end"] = {"dateTime": end}
    updated = service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
    print(json.dumps({
        "id": updated.get("id"),
        "summary": updated.get("summary"),
        "start": updated.get("start"),
        "end": updated.get("end"),
    }, indent=2))


def delete_event(service, calendar_id, event_id):
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    print(json.dumps({"deleted": True, "event_id": event_id, "calendar_id": calendar_id}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    sub.add_parser("list-calendars")
    p_create_cal = sub.add_parser("create-calendar")
    p_create_cal.add_argument("--name", default=DEFAULT_CALENDAR_NAME)
    p_create_cal.add_argument("--make-default", action="store_true")
    p_set_default = sub.add_parser("set-default-calendar")
    p_set_default.add_argument("--calendar-id", required=True)
    p_set_default.add_argument("--calendar-name")
    p_events = sub.add_parser("list-events")
    p_events.add_argument("--calendar-id")
    p_events.add_argument("--calendar-name")
    p_events.add_argument("--max-results", type=int, default=10)
    p_test = sub.add_parser("create-test-event")
    p_test.add_argument("--calendar-id")
    p_test.add_argument("--calendar-name")
    p_test.add_argument("--summary", default="OpenClaw test event")
    p_create = sub.add_parser("create-event")
    p_create.add_argument("--calendar-id")
    p_create.add_argument("--calendar-name")
    p_create.add_argument("--summary", required=True)
    p_create.add_argument("--start", required=True)
    p_create.add_argument("--end")
    p_create.add_argument("--all-day", action="store_true")
    p_create.add_argument("--description")
    p_create.add_argument("--location")
    p_all_day = sub.add_parser("make-event-all-day")
    p_all_day.add_argument("--calendar-id")
    p_all_day.add_argument("--calendar-name")
    p_all_day.add_argument("--event-id", required=True)
    p_all_day.add_argument("--day", help="YYYY-MM-DD; defaults to the event's current start date")
    p_update = sub.add_parser("update-event")
    p_update.add_argument("--calendar-id")
    p_update.add_argument("--calendar-name")
    p_update.add_argument("--event-id", required=True)
    p_update.add_argument("--summary")
    p_update.add_argument("--start")
    p_update.add_argument("--end")
    p_update.add_argument("--all-day", action="store_true")
    p_update.add_argument("--description")
    p_update.add_argument("--location")
    p_delete = sub.add_parser("delete-event")
    p_delete.add_argument("--calendar-id")
    p_delete.add_argument("--calendar-name")
    p_delete.add_argument("--event-id", required=True)
    args = parser.parse_args()

    service = load_service()
    if args.cmd == "auth":
        print("Auth OK")
    elif args.cmd == "list-calendars":
        list_calendars(service)
    elif args.cmd == "create-calendar":
        create_calendar(service, args.name, args.make_default)
    elif args.cmd == "set-default-calendar":
        set_default_calendar(args.calendar_id, args.calendar_name)
    elif args.cmd == "list-events":
        cal_id = resolve_calendar_id(service, args.calendar_id, args.calendar_name)
        list_events(service, cal_id, args.max_results)
    elif args.cmd == "create-test-event":
        cal_id = resolve_calendar_id(service, args.calendar_id, args.calendar_name)
        create_test_event(service, cal_id, args.summary)
    elif args.cmd == "create-event":
        cal_id = resolve_calendar_id(service, args.calendar_id, args.calendar_name)
        create_event(service, cal_id, args.summary, args.start, args.end, args.all_day, args.description, args.location)
    elif args.cmd == "make-event-all-day":
        cal_id = resolve_calendar_id(service, args.calendar_id, args.calendar_name)
        make_event_all_day(service, cal_id, args.event_id, args.day)
    elif args.cmd == "update-event":
        cal_id = resolve_calendar_id(service, args.calendar_id, args.calendar_name)
        update_event(service, cal_id, args.event_id, args.summary, args.start, args.end, args.all_day, args.description, args.location)
    elif args.cmd == "delete-event":
        cal_id = resolve_calendar_id(service, args.calendar_id, args.calendar_name)
        delete_event(service, cal_id, args.event_id)


if __name__ == "__main__":
    main()
