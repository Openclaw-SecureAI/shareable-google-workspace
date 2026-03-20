# Slides operations

Working directory:

```bash
cd ./google-workspace-integration
source .venv/bin/activate
```

Before first use:
- enable **Google Slides API** and **Google Drive API** in Google Cloud for the OAuth project
- for general setup and redirect handling, read `references/setup-auth.md`

One-time auth:

```bash
python3 slides_cli.py auth
```

Core commands:

```bash
python3 slides_cli.py create-presentation --title "Deck title"
python3 slides_cli.py get-presentation --presentation-id <PRESENTATION_ID>
python3 slides_cli.py add-title-slide --presentation-id <PRESENTATION_ID> --title "Conclusion title" --subtitle "Subtitle"
python3 slides_cli.py create-two-column-slide --presentation-id <PRESENTATION_ID> --title "The conclusion is clear" --left-heading "Problem" --left-bullets "Point 1" "Point 2" --right-heading "Solution" --right-bullets "Action 1" "Action 2"
python3 slides_cli.py create-title-and-chart-slide --presentation-id <PRESENTATION_ID> --title "The market is shifting" --insight "One key chart takeaway"
python3 slides_cli.py apply-theme --presentation-id <PRESENTATION_ID>
python3 slides_cli.py set-font-style --font-family Arial --title-pt 24 --body-pt 14
python3 slides_cli.py set-color-palette --primary-rgb 13 27 62 --accent-rgb 91 155 213 --neutral-rgb 102 102 102 --background-rgb 255 255 255
python3 slides_cli.py show-templates
python3 slides_cli.py duplicate-slide --presentation-id <PRESENTATION_ID> --slide-id <SLIDE_ID>
python3 slides_cli.py delete-slide --presentation-id <PRESENTATION_ID> --slide-id <SLIDE_ID>
```

Template system:
- Insight
- Problem / Solution
- Roadmap
- Data
- For Squareflow-specific work, prefer duplicating the approved template slides instead of drawing generic layouts over a square template canvas

Rules:
- titles should be conclusion-style, not vague labels
- keep bullets short and executive-readable
- use the shared Google Workspace integration root
- verify slide operations by reading the presentation metadata back
- presentation IDs come from create output or the Google Slides URL
- for Squareflow decks, duplicate the existing template slides first to preserve safe zones and layout geometry
