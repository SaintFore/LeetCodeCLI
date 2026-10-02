#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cli="$repo_root/.venv/bin/leetcode-fsrs"

if [[ ! -x "$cli" ]]; then
  echo "Missing $cli; install the project with .venv/bin/pip install -e '.[test]'" >&2
  exit 1
fi

smoke_tmp="$(mktemp -d)"
trap 'rm -rf -- "$smoke_tmp"' EXIT

export XDG_CONFIG_HOME="$smoke_tmp/config"
export XDG_DATA_HOME="$smoke_tmp/data"
export XDG_CACHE_HOME="$smoke_tmp/cache"
unset LEETCODE_SESSION || true

shared="$smoke_tmp/shared"
"$cli" --help >/dev/null
"$cli" init "$shared" --timezone UTC --username smoke-user >/dev/null

status_output="$("$cli" status)"
[[ "$status_output" == *"$shared"* ]]
[[ "$status_output" == *"smoke-user"* ]]

today_output="$("$cli" today --json)"
[[ "$today_output" == "[]" ]]

echo "CLI smoke test passed."
