# Setup and auth handoff

Use this when onboarding a new machine, account, or collaborator to the unified Google Workspace integration.

## Integration root

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

## Required local files

Expected under `~/.config/gog/`:

- `oauth-client.json` — Google OAuth client credentials
- per-service tokens such as:
  - `calendar-token.json`
  - `docs-drive-token.json`
  - `gmail-token.json`
  - `contacts-token.json`
  - `tasks-token.json`
  - `forms-token.json`

## Before auth: enable the APIs in Google Cloud

A valid OAuth client is not enough. Each Google API must also be enabled in the Google Cloud project used by `oauth-client.json`.

Typical symptom when forgotten:
- token refresh works
- API call fails with `403 PERMISSION_DENIED`
- error text mentions `SERVICE_DISABLED`, `accessNotConfigured`, or says the API has not been used/enabled for the project

Enable the APIs you plan to use in **Google Cloud Console → APIs & Services → Library** for the same project as the OAuth client.

Common APIs for this integration:
- Google Calendar API
- Google Drive API
- Google Docs API
- Google Sheets API
- Google Slides API
- Gmail API
- Google People API / Contacts
- Google Tasks API
- Google Forms API

Rule:
- if a service is being added or tested for the first time, verify its API is enabled before debugging auth or code

## Service auth pattern

Each service CLI follows this one-time pattern:

```bash
python <service>_cli.py auth
```

Example:

```bash
python tasks_cli.py auth
python contacts_cli.py auth
python forms_cli.py auth
```

## Important OAuth redirect rule

Some flows, especially Forms, use PKCE. The redirect URL must be pasted back into the **same live process** that generated the auth URL.

Correct flow:
1. run `python forms_cli.py auth`
2. copy the printed Google auth URL into the browser
3. approve access
4. copy the full redirect URL from the browser
5. paste it back into that same waiting terminal process

Do **not**:
- generate a fresh auth process and try to reuse an older redirect URL
- copy a redirect URL from one auth attempt into a different auth session

If done incorrectly, expect an error like:
- `invalid_grant`
- `Missing code verifier`

That does **not** usually mean the credentials are bad. It means the redirect URL was not paired with the original live auth session.

## Verification checklist after auth

After enabling the API and completing auth:
1. run a read/list command first
2. run one minimal write test only if needed
3. verify by reading back the created/updated object

Examples:
- Tasks: create one small test task, then list/get it
- Contacts: create one test contact, then fetch it directly by returned resource name
- Forms: create a small form, then fetch it and confirm `responderUri`

## Troubleshooting order

When a new service fails, check in this order:
1. correct Python environment (`source .venv/bin/activate`)
2. API enabled in Google Cloud for that project
3. token file exists under `~/.config/gog/`
4. auth was completed in the same live session when PKCE is involved
5. perform a minimal read call before a larger write workflow
