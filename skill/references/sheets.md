# Sheets operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google Sheets API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 sheets_cli.py auth
```

Core commands:

```bash
python3 sheets_cli.py create-sheet --title "Test Sheet"
python3 sheets_cli.py metadata --sheet-id <SHEET_ID>
python3 sheets_cli.py get-range --sheet-id <SHEET_ID> --range "Sheet1!A1:C10"
python3 sheets_cli.py update-range --sheet-id <SHEET_ID> --range "Sheet1!A1:B2" --values-json '[["A","B"],["1","2"]]'
python3 sheets_cli.py append-rows --sheet-id <SHEET_ID> --range "Sheet1!A:C" --values-json '[["x","y","z"]]'
python3 sheets_cli.py clear-range --sheet-id <SHEET_ID> --range "Sheet1!A2:Z"
```

Rules:
- use JSON values input for reliable automation
- verify writes by reading the affected range back
- get spreadsheet IDs from create output or the Google Sheets URL
