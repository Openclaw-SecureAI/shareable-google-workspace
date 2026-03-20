# Shareable Google Workspace Integration for OpenClaw

A reusable Google Workspace integration extracted from a working OpenClaw setup and cleaned for public sharing.

This repository includes two layers:
- `google-workspace-integration/` — Python CLIs for Google Calendar, Docs/Drive, Gmail, Contacts, Tasks, Sheets, Slides, and Forms
- `skill/` — the OpenClaw skill layer that shows an agent how to use the integration

## What is intentionally excluded

This repository does **not** include live credentials, tokens, account-specific configuration, local virtual environments, or private absolute paths.

Specifically excluded:
- `~/.config/gog/oauth-client.json`
- all `*-token.json` files
- account-specific calendar or task defaults
- `.venv/`, `__pycache__/`, and local machine state

## Repository layout

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
├── README.md
└── SETUP.md
```

## Quick start

### 1. Clone the repo and create a virtual environment

```bash
git clone <YOUR-REPO-URL>
cd shareable-google-workspace
python3 -m venv .venv
source .venv/bin/activate
pip install -r google-workspace-integration/requirements.txt
```

### 2. Create your Google OAuth client

Follow [`SETUP.md`](./SETUP.md). Store your downloaded desktop OAuth client JSON at:

```bash
mkdir -p ~/.config/gog
cp /path/to/downloaded-client.json ~/.config/gog/oauth-client.json
chmod 600 ~/.config/gog/oauth-client.json
```

Do not commit this file.

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
cd google-workspace-integration
python3 calendar_cli.py auth
```

### 5. Verify with a read command

```bash
python3 calendar_cli.py list-calendars
python3 gmail_cli.py list-messages --max-results 5
python3 tasks_cli.py list-tasklists
```

## Using this with OpenClaw

If you want OpenClaw to use this as a skill:

1. Copy `skill/` into your OpenClaw skills directory, or adapt it into your own workspace skill structure.
2. Update the skill paths if your repo lives somewhere else.
3. Ensure the Python dependencies are installed in the environment where OpenClaw will call the scripts.
4. Keep your live OAuth client and tokens outside the repo under `~/.config/gog/`.

A short installation note is available in [`examples/openclaw-skill-install.md`](./examples/openclaw-skill-install.md).

## Verification

Basic local verification:

```bash
bash scripts/verify_cli_help.sh
```

This confirms that each CLI parses and prints help without relying on private config files.

## Operational constraints

- First use of each service requires both API enablement **and** OAuth authorization.
- Some auth flows, especially Forms/PKCE-style flows, require pasting the redirect URL back into the same live terminal process.
- Token files are stored outside the repo at `~/.config/gog/`.
- This is a practical operator-oriented integration, not yet a polished Python package.

## Recommended future improvement

If you plan to publish this more widely, the next obvious improvement is a small shared auth/config module to remove repeated boilerplate across the per-service CLIs.
