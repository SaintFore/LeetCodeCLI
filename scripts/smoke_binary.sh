#!/usr/bin/env bash
set -euo pipefail

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="${1:-$repository_root/dist/leetcode-fsrs}"
if [[ ! -x "$binary" ]]; then
  echo "Missing binary: $binary" >&2
  exit 1
fi

smoke_root=$(mktemp -d)
trap 'rm -rf -- "$smoke_root"' EXIT
export XDG_CONFIG_HOME="$smoke_root/config"
export XDG_DATA_HOME="$smoke_root/data"
export XDG_CACHE_HOME="$smoke_root/cache"
unset LEETCODE_SESSION || true

shared="$smoke_root/shared"
"$binary" --help >/dev/null
"$binary" init "$shared" --timezone UTC --username binary-smoke >/dev/null
status_output=$("$binary" status)
[[ "$status_output" == *"$shared"* ]]
[[ "$status_output" == *"binary-smoke"* ]]
[[ "$("$binary" today --json)" == "[]" ]]

echo "Binary smoke test passed."
