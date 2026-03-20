# Gmail operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Gmail API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 gmail_cli.py auth
```

Core commands:

```bash
python3 gmail_cli.py list-messages --max-results 10
python3 gmail_cli.py list-messages --query "is:unread"
python3 gmail_cli.py get-message --message-id <MESSAGE_ID>
python3 gmail_cli.py draft-message --to person@example.com --subject "Hello" --body "Draft body"
python3 gmail_cli.py send-message --to person@example.com --subject "Hello" --body "Body"
python3 gmail_cli.py modify-labels --message-id <MESSAGE_ID> --add-label STARRED
```

Rules:
- reading/listing is lower risk than sending
- drafting is preferred before sending on the user's behalf
- verify drafts/sends by fetching the resulting message or checking message listing
- be careful with `send-message`; confirm intent clearly in normal use
