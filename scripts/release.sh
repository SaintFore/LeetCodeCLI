#!/bin/bash

# release.sh - Automate version bumping and tagging

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.4.1"
    exit 1
fi

NEW_VERSION="$1"

# Validate version format (simple check)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Version must be in format X.Y.Z"
    exit 1
fi

echo "🚀 Preparing release v$NEW_VERSION..."

# 1. Update setup.py
sed -i "s/version=\"[0-9.]*\"/version=\"$NEW_VERSION\"/" setup.py
echo "✅ Updated setup.py"

# 2. Update version.py
sed -i "s/__version__ = \"[0-9.]*\"/__version__ = \"$NEW_VERSION\"/" leetcode_fsrs_cli/version.py
echo "✅ Updated leetcode_fsrs_cli/version.py"

# 3. Update README.md (badge)
sed -i "s/version-[0-9.]*-blue/version-$NEW_VERSION-blue/" README.md
echo "✅ Updated README.md"

# 4. Update PKGBUILD (local copy)
sed -i "s/^pkgver=.*/pkgver=$NEW_VERSION/" aur-assets/PKGBUILD
sed -i "s/^pkgver=.*/pkgver=$NEW_VERSION/" aur-assets/PKGBUILD.bin
echo "✅ Updated aur-assets/PKGBUILD & PKGBUILD.bin"

# 5. Git operations
echo "📦 Committing changes..."
git add .
git commit -m "chore: release v$NEW_VERSION"

echo "🏷️ Creating tag v$NEW_VERSION..."
git tag -f "v$NEW_VERSION"

echo "🚀 Pushing to GitHub..."
git push origin main
git push origin "v$NEW_VERSION" --force

echo "✨ Release v$NEW_VERSION published!"
echo "⏳ GitHub Actions will now automatically update the AUR package."
