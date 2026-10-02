#!/usr/bin/env bash
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
venv_bin="$repo_root/.venv/bin"

required=(python ruff pyright pytest leetcode-fsrs)
for command_name in "${required[@]}"; do
  if [[ ! -x "$venv_bin/$command_name" ]]; then
    echo "Missing $venv_bin/$command_name" >&2
    echo "Create the environment and install checks with:" >&2
    echo "  python3 -m venv .venv" >&2
    echo "  .venv/bin/pip install -e '.[test]'" >&2
    exit 1
  fi
done

cd "$repo_root"
failures=()

run_check() {
  local name="$1"
  shift
  echo
  echo "==> $name"
  if "$@"; then
    echo "PASS: $name"
  else
    echo "FAIL: $name"
    failures+=("$name")
  fi
}

run_check "Ruff lint" "$venv_bin/ruff" check .
run_check "Ruff format" "$venv_bin/ruff" format --check .
run_check "Pyright" "$venv_bin/pyright"
run_check "pytest" "$venv_bin/pytest" -q
run_check "CLI smoke" "$repo_root/scripts/smoke_test.sh"

echo
if (( ${#failures[@]} > 0 )); then
  echo "Checks failed: ${failures[*]}"
  exit 1
fi

echo "All checks passed."
