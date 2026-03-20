# Service matrix

Use this as the fast handoff checklist for the unified Google Workspace integration.

## Shared prerequisites

For all services:
- use the integration root: `./google-workspace-integration`
- activate the shared virtualenv: `source .venv/bin/activate`
- ensure `~/.config/gog/oauth-client.json` exists
- enable the corresponding Google API in the same Google Cloud project
- complete `python <service>_cli.py auth`
- test with one minimal read command before larger writes

## Service-by-service map

### Calendar
- CLI: `calendar_cli.py`
- token: `~/.config/gog/calendar-token.json`
- extra config: `~/.config/gog/calendar-config.json`
- enable: **Google Calendar API**
- first verification:
  - `python3 calendar_cli.py list-calendars`
  - `python3 calendar_cli.py list-events --max-results 5`

### Docs + Drive
- CLI: `docs_drive_cli.py`
- token: `~/.config/gog/docs-drive-token.json`
- enable:
  - **Google Drive API**
  - **Google Docs API**
- first verification:
  - `python3 docs_drive_cli.py search-drive --query "test"`
  - or create one tiny doc and read it back

### Gmail
- CLI: `gmail_cli.py`
- token: `~/.config/gog/gmail-token.json`
- enable: **Gmail API**
- first verification:
  - `python3 gmail_cli.py list-messages --max-results 5`

### Contacts
- CLI: `contacts_cli.py`
- token: `~/.config/gog/contacts-token.json`
- enable: **Google People API**
- first verification:
  - `python3 contacts_cli.py list-contacts --page-size 5`
  - `python3 contacts_cli.py search-contacts --query "Alice"`

### Tasks
- CLI: `tasks_cli.py`
- token: `~/.config/gog/tasks-token.json`
- enable: **Google Tasks API**
- first verification:
  - `python3 tasks_cli.py list-tasklists`

### Sheets
- CLI: `sheets_cli.py`
- token: `~/.config/gog/sheets-token.json`
- enable: **Google Sheets API**
- first verification:
  - create one small sheet or read metadata from an existing one

### Slides
- CLI: `slides_cli.py`
- token: `~/.config/gog/slides-token.json`
- local theme file: `./google-workspace-integration/slides-theme.json`
- enable:
  - **Google Slides API**
  - **Google Drive API**
- first verification:
  - `python3 slides_cli.py create-presentation --title "Test deck"`
  - `python3 slides_cli.py get-presentation --presentation-id <PRESENTATION_ID>`

### Forms
- CLI: `forms_cli.py`
- token: `~/.config/gog/forms-token.json`
- enable:
  - **Google Forms API**
  - **Google Drive API**
- first verification:
  - `python3 forms_cli.py list-forms --page-size 5`
  - or create one tiny form and fetch it back

## Common failure signatures

- `403 PERMISSION_DENIED` + `SERVICE_DISABLED` / `accessNotConfigured`
  - the API is not enabled in Google Cloud for that project

- `invalid_grant` + `Missing code verifier`
  - the OAuth redirect URL was pasted into the wrong auth session
  - rerun `python <service>_cli.py auth` and paste the redirect URL back into that same waiting process
