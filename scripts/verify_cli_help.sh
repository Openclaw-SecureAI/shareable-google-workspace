#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../google-workspace-integration"
for f in *_cli.py; do
  echo "==> $f"
  python3 "$f" --help >/dev/null
done
echo "CLI help verification passed"
