# Setup Guide

This guide is for a new user starting from zero.

## 1. Prerequisites

- Python 3.10+
- A Google account you control
- Access to Google Cloud Console
- Terminal access on the machine where you want to run the integration

## 2. Create a Google Cloud project

1. Open Google Cloud Console.
2. Create a new project or choose an existing one dedicated to this integration.
3. Confirm billing/project policy on your side if your org requires it.

## 3. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Choose **External** unless you are operating fully inside a Google Workspace org and want Internal.
3. Fill app name, support email, and developer contact email.
4. Add yourself as a test user if the app is still in testing.
5. Save.

## 4. Create OAuth client credentials

1. Go to **APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth client ID**.
3. Application type: **Desktop app**.
4. Download the JSON file.
5. Store it here:

```bash
mkdir -p ~/.config/gog
cp /path/to/downloaded-client.json ~/.config/gog/oauth-client.json
chmod 600 ~/.config/gog/oauth-client.json
```

Do not commit this file.

## 5. Enable the required APIs

Enable only the services you plan to use, or enable the full set:

- Google Calendar API
- Google Drive API
- Google Docs API
- Gmail API
- Google People API
- Google Tasks API
- Google Sheets API
- Google Slides API
- Google Forms API

If you skip this, auth may succeed but API calls can still fail with:
- `403 PERMISSION_DENIED`
- `SERVICE_DISABLED`
- `accessNotConfigured`

## 6. Install Python dependencies

From the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r google-workspace-integration/requirements.txt
```

## 7. Run auth for one service

Example for Calendar:

```bash
cd google-workspace-integration
python3 calendar_cli.py auth
```

The CLI prints a Google auth URL.

1. Open the URL in your browser.
2. Approve the requested scopes.
3. Google redirects to `http://localhost/?...`.
4. Copy the full redirect URL.
5. Paste it back into the same waiting terminal process.

### Important PKCE/session rule

Do not paste a redirect URL into a different auth process from the one that generated it.
That can fail with `invalid_grant` or `Missing code verifier`.

## 8. Verify each service

### Calendar
```bash
python3 calendar_cli.py list-calendars
python3 calendar_cli.py list-events --max-results 5
```

### Docs + Drive
```bash
python3 docs_drive_cli.py search-drive --query "test"
```

### Gmail
```bash
python3 gmail_cli.py list-messages --max-results 5
```

### Contacts
```bash
python3 contacts_cli.py list-contacts --page-size 5
```

### Tasks
```bash
python3 tasks_cli.py list-tasklists
```

### Sheets
```bash
python3 sheets_cli.py --help
```

### Slides
```bash
python3 slides_cli.py --help
```

### Forms
```bash
python3 forms_cli.py list-forms --page-size 5
```

## 9. Install into OpenClaw

You have two realistic options.

### Option A: keep this repo standalone and point a local skill at it

- clone the repo where you want it
- copy `skill/SKILL.md` and `skill/references/` into your OpenClaw skills area
- edit any repo paths in the skill if needed

### Option B: vendor the repo contents into your OpenClaw workspace

- copy `google-workspace-integration/` into your workspace
- copy the skill into your workspace skills directory
- keep credentials in `~/.config/gog/`

## 10. Troubleshooting

### Problem: auth worked but commands fail with 403
Likely cause: API not enabled in Google Cloud.

### Problem: `Missing code verifier` or `invalid_grant`
Likely cause: redirect URL pasted into the wrong still-running auth process.

### Problem: `FileNotFoundError` for `oauth-client.json`
Create `~/.config/gog/oauth-client.json` from your downloaded desktop OAuth client JSON.

### Problem: token exists but commands still fail
Delete only the affected token file and rerun `auth` for that service.
Do not delete everything blindly.

### Problem: OpenClaw can’t find the scripts
Your skill paths are wrong for your installation. Make them repo-relative or absolute for your machine.
