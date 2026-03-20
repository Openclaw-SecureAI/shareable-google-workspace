# Migration notes

Canonical production integration root:

`./google-workspace-integration`

Retired paths and why:
- `google-calendar-integration/` — initial prototype path; replaced by the unified Google workspace integration root
- `skills/gog/` — useful as inspiration, but not suitable for routine headless VPS operations because of interactive callback/keyring behavior

What was worth preserving from gog:
- Drive search ideas
- Sheets metadata/update/append/clear concepts
- Docs export/read concepts
- preference for structured, scriptable operations

Do not route future production Google actions through `gog` unless the operational constraints change significantly.
