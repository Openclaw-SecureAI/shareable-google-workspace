# Forms operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google Forms API** in Google Cloud for the OAuth project
- also keep **Google Drive API** enabled because form listing uses Drive metadata search
- for auth flow details and PKCE redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 forms_cli.py auth
```

Core commands:

```bash
python3 forms_cli.py list-forms --page-size 20
python3 forms_cli.py create-form --title "Test form"
python3 forms_cli.py get-form --form-id <FORM_ID>
python3 forms_cli.py update-form-info --form-id <FORM_ID> --description "Short description"
python3 forms_cli.py add-text-question --form-id <FORM_ID> --title "Your name" --required
python3 forms_cli.py add-choice-question --form-id <FORM_ID> --title "Do you know OpenClaw?" --option Yes --option No --question-type RADIO --required
python3 forms_cli.py list-responses --form-id <FORM_ID>
```

Rules:
- auth must complete in the same live terminal session that printed the auth URL
- after creating or updating a form, verify by fetching it again
- use explicit `FORM_ID` values from create output or the Google Forms URL
- listing forms relies on Drive metadata because Forms itself is weak for global listing
