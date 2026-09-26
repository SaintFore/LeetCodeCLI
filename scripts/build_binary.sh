#!/usr/bin/env bash
set -euo pipefail

python -m pip install . pyinstaller
python -m PyInstaller \
  --clean \
  --onefile \
  --name leetcode-fsrs \
  --collect-all textual \
  --collect-all fsrs \
  --collect-all keyring \
  scripts/pyinstaller_entry.py

echo "Built dist/leetcode-fsrs"
