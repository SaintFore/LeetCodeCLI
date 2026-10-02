#!/usr/bin/env bash
set -euo pipefail

version="${1:-}"
archive="${2:-}"
if [[ ! "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || [[ ! -f "$archive" ]]; then
  echo "Usage: $0 X.Y.Z PATH/TO/leetcode-fsrs-X.Y.Z-linux-x86_64.tar.gz" >&2
  exit 2
fi

repository_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
archive=$(realpath "$archive")
checksum=$(sha256sum "$archive" | cut -d ' ' -f1)
build_root=$(mktemp -d)
trap 'rm -rf -- "$build_root"' EXIT

python "$repository_root/scripts/render_aur_bin.py" \
  "$version" "$checksum" --output "$build_root/PKGBUILD"
cp "$archive" "$build_root/leetcode-fsrs-bin-${version}.tar.gz"
(
  cd "$build_root"
  makepkg --printsrcinfo > .SRCINFO
  makepkg --cleanbuild --force
)

package=$(
  find "$build_root" -maxdepth 1 \
    -name "leetcode-fsrs-bin-${version}-*.pkg.tar.zst" \
    ! -name '*-debug-*' -print -quit
)
if [[ -z "$package" ]]; then
  echo "makepkg did not produce a package" >&2
  exit 1
fi
install -m644 "$package" "$repository_root/packaging/aur-bin/$(basename "$package")"
echo "Built packaging/aur-bin/$(basename "$package")"
