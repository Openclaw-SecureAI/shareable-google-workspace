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
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/contacts",
]
CONFIG_DIR = Path.home() / ".config" / "gog"
CLIENT_FILE = CONFIG_DIR / "oauth-client.json"
TOKEN_FILE = CONFIG_DIR / "contacts-token.json"


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


def people_service():
    return build("people", "v1", credentials=load_creds())


def auth():
    load_creds()
    print("Auth OK")


def list_contacts(page_size=20):
    service = people_service()
    res = service.people().connections().list(
        resourceName="people/me",
        pageSize=page_size,
        personFields="names,emailAddresses,phoneNumbers,organizations"
    ).execute()
    out = []
    for p in res.get("connections", []):
        out.append({
            "resourceName": p.get("resourceName"),
            "name": (p.get("names") or [{}])[0].get("displayName"),
            "email": (p.get("emailAddresses") or [{}])[0].get("value"),
            "phone": (p.get("phoneNumbers") or [{}])[0].get("value"),
            "organization": (p.get("organizations") or [{}])[0].get("name"),
        })
    print(json.dumps(out, indent=2))


def get_contact(resource_name):
    service = people_service()
    person = service.people().get(
        resourceName=resource_name,
        personFields="names,emailAddresses,phoneNumbers,organizations,biographies,addresses"
    ).execute()
    print(json.dumps(person, indent=2))


def search_contacts(query, page_size=10):
    service = people_service()
    res = service.people().searchContacts(
        query=query,
        pageSize=page_size,
        readMask="names,emailAddresses,phoneNumbers,organizations"
    ).execute()
    out = []
    for r in res.get("results", []):
        p = r.get("person", {})
        out.append({
            "resourceName": p.get("resourceName"),
            "name": (p.get("names") or [{}])[0].get("displayName"),
            "email": (p.get("emailAddresses") or [{}])[0].get("value"),
            "phone": (p.get("phoneNumbers") or [{}])[0].get("value"),
            "organization": (p.get("organizations") or [{}])[0].get("name"),
        })
    print(json.dumps(out, indent=2))


def create_contact(given_name, family_name=None, email=None, phone=None, organization=None):
    service = people_service()
    body = {"names": [{"givenName": given_name}]}
    if family_name:
        body["names"][0]["familyName"] = family_name
    if email:
        body["emailAddresses"] = [{"value": email}]
    if phone:
        body["phoneNumbers"] = [{"value": phone}]
    if organization:
        body["organizations"] = [{"name": organization}]
    created = service.people().createContact(body=body).execute()
    resource_name = created.get("resourceName")
    verified = None
    if resource_name:
        verified = service.people().get(
            resourceName=resource_name,
            personFields="names,emailAddresses,phoneNumbers,organizations,metadata"
        ).execute()
    print(json.dumps({
        "created": created,
        "verified_fetch": verified,
        "note": "Direct verification succeeded if verified_fetch is populated. Google UI/search visibility may still lag."
    }, indent=2))


def update_contact(resource_name, etag, given_name=None, family_name=None, email=None, phone=None, organization=None):
    service = people_service()
    body = {"resourceName": resource_name, "etag": etag}
    if given_name or family_name:
        n = {}
        if given_name:
            n["givenName"] = given_name
        if family_name:
            n["familyName"] = family_name
        body["names"] = [n]
    if email is not None:
        body["emailAddresses"] = [{"value": email}] if email else []
    if phone is not None:
        body["phoneNumbers"] = [{"value": phone}] if phone else []
    if organization is not None:
        body["organizations"] = [{"name": organization}] if organization else []
    updated = service.people().updateContact(
        resourceName=resource_name,
        updatePersonFields="names,emailAddresses,phoneNumbers,organizations",
        body=body,
    ).execute()
    print(json.dumps(updated, indent=2))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")

    p_list = sub.add_parser("list-contacts")
    p_list.add_argument("--page-size", type=int, default=20)

    p_get = sub.add_parser("get-contact")
    p_get.add_argument("--resource-name", required=True)

    p_search = sub.add_parser("search-contacts")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--page-size", type=int, default=10)

    p_create = sub.add_parser("create-contact")
    p_create.add_argument("--given-name", required=True)
    p_create.add_argument("--family-name")
    p_create.add_argument("--email")
    p_create.add_argument("--phone")
    p_create.add_argument("--organization")

    p_update = sub.add_parser("update-contact")
    p_update.add_argument("--resource-name", required=True)
    p_update.add_argument("--etag", required=True)
    p_update.add_argument("--given-name")
    p_update.add_argument("--family-name")
    p_update.add_argument("--email")
    p_update.add_argument("--phone")
    p_update.add_argument("--organization")

    args = parser.parse_args()

    if args.cmd == "auth":
        auth()
    elif args.cmd == "list-contacts":
        list_contacts(args.page_size)
    elif args.cmd == "get-contact":
        get_contact(args.resource_name)
    elif args.cmd == "search-contacts":
        search_contacts(args.query, args.page_size)
    elif args.cmd == "create-contact":
        create_contact(args.given_name, args.family_name, args.email, args.phone, args.organization)
    elif args.cmd == "update-contact":
        update_contact(args.resource_name, args.etag, args.given_name, args.family_name, args.email, args.phone, args.organization)


if __name__ == "__main__":
    main()
