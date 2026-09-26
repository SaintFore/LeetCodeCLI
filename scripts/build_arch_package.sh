#!/usr/bin/env bash
set -euo pipefail

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

paru -B "$repository_root/packaging/aur-git" "$@"

echo "Package built under packaging/aur-git/. Use -i to install it:"
echo "  scripts/build_arch_package.sh -i"
