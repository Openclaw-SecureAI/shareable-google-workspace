# Tasks operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google Tasks API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 tasks_cli.py auth
```

Core commands:

```bash
python3 tasks_cli.py list-tasklists
python3 tasks_cli.py create-tasklist --title "My list"
python3 tasks_cli.py list-tasks --tasklist-id <TASKLIST_ID>
python3 tasks_cli.py create-task --tasklist-id <TASKLIST_ID> --title "Test task"
python3 tasks_cli.py get-task --tasklist-id <TASKLIST_ID> --task-id <TASK_ID>
python3 tasks_cli.py update-task --tasklist-id <TASKLIST_ID> --task-id <TASK_ID> --status completed
python3 tasks_cli.py delete-task --tasklist-id <TASKLIST_ID> --task-id <TASK_ID>
```

Rules:
- listing and reading are lower risk than create/update/delete
- tasklist IDs and task IDs should be treated explicitly to avoid ambiguity
- after creating or updating, verify with `get-task` or `list-tasks`
- deleting tasks is state-changing; be deliberate in normal use
