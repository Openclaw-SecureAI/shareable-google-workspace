---
name: google-workspace
description: Headless Google Workspace operations for a reusable OpenClaw/VPS integration. Use when the user wants Google Calendar, Docs, Drive, Gmail, Contacts, Tasks, Sheets, Slides, or Forms actions executed from the VPS without relying on gog, browser-dependent local shells, or interactive keyrings. Prefer this skill for creating, editing, listing, searching, and verifying Google resources through the custom Python integration under ./google-workspace-integration.
---

# Google Workspace

Use the unified custom Google integration in this repo:

`./google-workspace-integration`

This is the production path.
Do **not** prefer `gog` for routine operations in this environment.

## Working directory

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

## Current components

- `calendar_cli.py` — Calendar operations
- `docs_drive_cli.py` — Docs + Drive operations, including folders, uploads, downloads, copy, sharing, and permissions
- `sheets_cli.py` — Sheets operations
- `slides_cli.py` — Slides operations with theme, template, and consulting-style slide helpers
- `gmail_cli.py` — Gmail operations
- `contacts_cli.py` — Contacts / People operations
- `tasks_cli.py` — Tasks operations
- `forms_cli.py` — Forms operations

## Auth and tokens

Token/config files live under:

```bash
~/.config/gog/
```

Current files used by the custom integration include:
- `oauth-client.json`
- `calendar-token.json`
- `calendar-config.json`
- `docs-drive-token.json`
- `gmail-token.json`
- `contacts-token.json`
- `tasks-token.json`
- `forms-token.json`

Do not modify OAuth/token files unless the user asks.

## Critical onboarding rules

Before debugging a new Google service, read `references/setup-auth.md`.

Two recurring failure modes matter here:

1. **API not enabled in Google Cloud**
   - OAuth/token presence does not mean the API itself is enabled.
   - A missing API commonly appears as `403 PERMISSION_DENIED`, `SERVICE_DISABLED`, or `accessNotConfigured`.
   - For a new service, verify the corresponding API is enabled in the Google Cloud project used by `oauth-client.json` before assuming the code is broken.

2. **OAuth redirect URL reused in the wrong session**
   - Some services, especially Forms, use PKCE.
   - The redirect URL must be pasted back into the same live `python <service>_cli.py auth` process that generated the Google auth URL.
   - Reusing a redirect URL in a different session can fail with `invalid_grant` / `Missing code verifier`.

## Operating rules

- Prefer the custom Python integration over `gog`.
- For destructive actions, identify the target precisely before acting.
- After any write, verify by reading back the changed object or searching for it.
- Keep Google service scripts grouped under the shared integration root; do not create new scattered per-service directories unless there is a strong reason.

## References

Read as needed:
- `references/setup-auth.md` — onboarding, API enablement, OAuth redirect handling, troubleshooting order
- `references/service-matrix.md` — service-by-service API/token/verification checklist
- `references/calendar.md`
- `references/docs-drive.md`
- `references/slides.md`
- `references/gmail.md`
- `references/contacts.md`
- `references/tasks.md`
- `references/forms.md`
- `references/sheets.md`
- `references/migration-notes.md`
