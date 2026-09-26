#!/usr/bin/env bash
set -euo pipefail

version="${1:-}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: $0 X.Y.Z" >&2
  exit 2
fi

sed -i -E "s/^version = \"[0-9.]+\"/version = \"$version\"/" pyproject.toml
sed -i -E "s/^__version__ = \"[0-9.]+\"/__version__ = \"$version\"/" leetcode_fsrs/__init__.py

echo "Updated version metadata to $version. Review, commit, and tag v$version manually."
