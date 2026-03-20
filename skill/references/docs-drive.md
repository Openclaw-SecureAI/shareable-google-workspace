# Docs + Drive operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google Drive API** and **Google Docs API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 docs_drive_cli.py auth
```

Core commands:

```bash
python3 docs_drive_cli.py create-doc --title "test doc"
python3 docs_drive_cli.py write-doc --doc-id <DOC_ID> --text "it worked"
python3 docs_drive_cli.py get-doc --doc-id <DOC_ID>
python3 docs_drive_cli.py search-drive --query "test doc"
python3 docs_drive_cli.py list-folder --folder-id root
python3 docs_drive_cli.py create-folder --name "Shared"
python3 docs_drive_cli.py upload-file --local-path ./local.txt --parent-id <FOLDER_ID>
python3 docs_drive_cli.py get-file --file-id <FILE_ID>
python3 docs_drive_cli.py move-file --file-id <FILE_ID> --add-parent-id <FOLDER_ID>
python3 docs_drive_cli.py copy-file --file-id <FILE_ID> --name "Copy"
python3 docs_drive_cli.py download-file --file-id <FILE_ID> --output-path ./downloaded.bin
python3 docs_drive_cli.py export-google-doc --file-id <FILE_ID> --output-path ./doc.pdf
python3 docs_drive_cli.py share-file --file-id <FILE_ID> --email person@example.com --role writer
python3 docs_drive_cli.py set-permission --file-id <FILE_ID> --anyone --role reader
```

Rules:
- create Docs through the custom Python path, not `gog`
- after writing, read back the document to verify content
- verify Drive visibility with `search-drive` or `list-folder`
- document IDs come from create output or the Google Docs URL
- folder/file sharing and permissions are sensitive; confirm intent before broad sharing in normal use
