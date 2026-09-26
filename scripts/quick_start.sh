#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/pytest -q

echo "Run .venv/bin/leetcode-fsrs to start the TUI."
