# Calendar operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google Calendar API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 calendar_cli.py auth
```

Core commands:

```bash
python3 calendar_cli.py list-calendars
python3 calendar_cli.py create-calendar --name "My Calendar"
python3 calendar_cli.py set-default-calendar --calendar-id <CALENDAR_ID>
python3 calendar_cli.py list-events --max-results 10
python3 calendar_cli.py create-event --summary "..." --start "..." --end "..."
python3 calendar_cli.py create-event --summary "..." --start "YYYY-MM-DD" --all-day
python3 calendar_cli.py update-event --event-id <EVENT_ID> ...
python3 calendar_cli.py make-event-all-day --event-id <EVENT_ID> [--day YYYY-MM-DD]
python3 calendar_cli.py delete-event --event-id <EVENT_ID>
```

Conventions:
- timed events use RFC3339-ish timestamps
- all-day events use `YYYY-MM-DD` + `--all-day`
- prefer the configured default calendar unless the user specifies another target
- after creating or updating, verify by listing events or fetching the target again
- confirm destructive deletes when the target is ambiguous
