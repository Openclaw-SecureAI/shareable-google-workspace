# Contacts operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google People API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 contacts_cli.py auth
```

Core commands:

```bash
python3 contacts_cli.py list-contacts --page-size 20
python3 contacts_cli.py search-contacts --query "Alice"
python3 contacts_cli.py get-contact --resource-name people/c123456789
python3 contacts_cli.py create-contact --given-name Alice --family-name Example --email alice@example.com
python3 contacts_cli.py update-contact --resource-name people/c123456789 --etag <ETAG> --phone "+32..."
```

Rules:
- searching and listing are lower risk than creating/updating
- updating requires the current resource name and etag
- after creating or updating, verify by direct fetch using the returned resource name
- Google UI/search visibility can lag behind direct API success
- contact creation/update is state-changing; be deliberate in normal use
