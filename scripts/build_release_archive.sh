#!/usr/bin/env bash
set -euo pipefail

version="${1:-}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Usage: $0 X.Y.Z" >&2
  exit 2
fi

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
binary="$repository_root/dist/leetcode-fsrs"
if [[ ! -x "$binary" ]]; then
  echo "Missing executable $binary; run scripts/build_binary.sh first" >&2
  exit 1
fi

release_root="$repository_root/dist/leetcode-fsrs-${version}-linux-x86_64"
archive="$release_root.tar.gz"
rm -rf -- "$release_root"
mkdir -p "$release_root"
install -m755 "$binary" "$release_root/leetcode-fsrs"
install -m644 "$repository_root/packaging/desktop/leetcode-fsrs.desktop" "$release_root/leetcode-fsrs.desktop"
install -m644 "$repository_root/output/openai-image/leetcode-fsrs-icon.png" "$release_root/leetcode-fsrs.png"
install -m644 "$repository_root/LICENSE" "$release_root/LICENSE"
tar --sort=name --owner=0 --group=0 --numeric-owner -czf "$archive" -C "$repository_root/dist" "$(basename "$release_root")"
(cd "$repository_root/dist" && sha256sum "$(basename "$archive")" > SHA256SUMS)

echo "Built $archive"
echo "Wrote $repository_root/dist/SHA256SUMS"
