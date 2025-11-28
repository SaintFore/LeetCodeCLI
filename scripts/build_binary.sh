#!/bin/bash

# Binary build script for leetcode-fsrs-cli
# This script creates a standalone binary using PyInstaller

set -e

echo "Building leetcode-fsrs-cli binary..."

# Install PyInstaller if not present
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    python3 -m pip install pyinstaller
fi

# Install dependencies for building
python3 -m pip install -r requirements.txt

# Create binary with PyInstaller
echo "Creating standalone binary..."
pyinstaller --onefile \
    --name leetcode-fsrs \
    --add-data "leetcode_fsrs_cli/data/*.json:leetcode_fsrs_cli/data" \
    leetcode_fsrs_cli/cli.py

# Move binary to current directory
cp dist/leetcode-fsrs ./

# Create binary package name
BINARY_NAME="leetcode-fsrs-cli-1.0.0-1-x86_64"
mv leetcode-fsrs "$BINARY_NAME"

# Calculate checksum
CHECKSUM=$(sha256sum "$BINARY_NAME" | cut -d' ' -f1)
echo "Binary checksum: $CHECKSUM"

# Update PKGBUILD.bin with checksum
sed -i "s/sha256sums=('SKIP')/sha256sums=('$CHECKSUM')/" aur-repo/PKGBUILD.bin

# Create binary package using makepkg
cd aur-repo
cp ../"$BINARY_NAME" ./
mv PKGBUILD.bin PKGBUILD
makepkg

# Rename back
mv PKGBUILD PKGBUILD.bin

# Clean up
cd ..
rm -rf build/ dist/ "$BINARY_NAME"

echo "Binary package created successfully!"
echo "Package file: aur-repo/leetcode-fsrs-cli-bin-1.0.0-1-x86_64.pkg.tar.zst"