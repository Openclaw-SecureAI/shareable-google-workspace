# Shareable Google Workspace Integration for OpenClaw

Reusable Google Workspace integration packaged from an internal OpenClaw setup, cleaned for public sharing.

This repo contains two layers:

- `google-workspace-integration/` — Python CLIs for Google Calendar, Docs/Drive, Gmail, Contacts, Tasks, Sheets, Slides, and Forms
- `skill/` — the OpenClaw skill/instruction layer showing how an agent should use the integration

## What this repo intentionally does **not** include

No live credentials, tokens, account-specific configs, local virtualenvs, or private workspace paths.

Specifically excluded:

- `~/.config/gog/oauth-client.json`
- all `*-token.json` files
- account-specific calendar/task defaults
- `.venv/`, `__pycache__/`, or local machine state

## Repo layout

```text
shareable-google-workspace/
├── google-workspace-integration/
│   ├── calendar_cli.py
│   ├── contacts_cli.py
│   ├── docs_drive_cli.py
│   ├── forms_cli.py
│   ├── gmail_cli.py
│   ├── requirements.txt
│   ├── sheets_cli.py
│   ├── slides_cli.py
│   ├── slides-theme.json
│   └── tasks_cli.py
├── skill/
│   ├── SKILL.md
│   └── references/
├── examples/
│   ├── oauth-client.example.json
│   └── openclaw-skill-install.md
├── scripts/
│   └── verify_cli_help.sh
├── .gitignore
└── SETUP.md
```

## Quick start

### 1. Clone and create a virtualenv

```bash
git clone <YOUR-REPO-URL>
cd shareable-google-workspace/python3 -m venv .venv
source .venv/bin/activate
pip install -r google-workspace-integration/requirements.txt
```

### 2. Create your Google OAuth client

Follow [`SETUP.md`](./SETUP.md). Put your downloaded OAuth desktop client JSON at:

```bash
mkdir -p ~/.config/gog
cp examples/oauth-client.example.json ~/.config/gog/oauth-client.json
# then replace that example file with the real client JSON downloaded from Google Cloud
```

### 3. Enable the Google APIs you need

Common APIs:
- Google Calendar API
- Google Drive API
- Google Docs API
- Gmail API
- Google People API
- Google Tasks API
- Google Sheets API
- Google Slides API
- Google Forms API

### 4. Authenticate one service

```bash
source .venv/bin/activate
cd google-workspace-integration
python3 calendar_cli.py auth
```

### 5. Verify with a read command

```bash
python3 calendar_cli.py list-calendars
python3 gmail_cli.py list-messages --max-results 5
python3 tasks_cli.py list-tasklists
```

## OpenClaw install/use

If you want OpenClaw to use this as a skill:

1. copy `skill/` into your OpenClaw skills directory, or adapt it into your own workspace skill structure
2. update the skill paths if your repo lives somewhere else
3. ensure the Python dependencies are installed in the environment where OpenClaw will call the scripts
4. keep your live OAuth client and tokens outside the repo under `~/.config/gog/`

A short install note is in [`examples/openclaw-skill-install.md`](./examples/openclaw-skill-install.md).

## Verification

Basic local verification:

```bash
bash scripts/verify_cli_help.sh
```

This checks that each CLI parses and prints help without importing private config files.

## Known operational constraints

- First use of each service requires both API enablement **and** OAuth authorization.
- Some auth flows, especially Forms/PKCE-style flows, require pasting the redirect URL back into the same live terminal process.
- Token files are stored outside the repo at `~/.config/gog/`.
- This is a practical operator-oriented integration, not a polished Python package yet.

## Recommended next improvement if publishing widely

Add a small shared auth/config module to remove repeated boilerplate across the per-service CLIs.
