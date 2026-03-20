# OpenClaw skill install notes

Suggested pattern:

1. Clone this repo to a stable path.
2. Copy `skill/` into your OpenClaw skills directory.
3. Update path references inside `SKILL.md` and `references/` if your integration lives elsewhere.
4. Ensure your runtime can execute the Python scripts with the required dependencies installed.
5. Keep OAuth client + tokens under `~/.config/gog/`, not inside the repo.

Minimal validation:

```bash
cd <repo>/google-workspace-integration
python3 calendar_cli.py --help
python3 docs_drive_cli.py --help
python3 gmail_cli.py --help
```
