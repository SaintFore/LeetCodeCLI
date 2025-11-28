#!/bin/bash

# Simple binary build script using system tools
# This creates a basic binary package without PyInstaller

echo "Creating simple binary package..."

# Create a simple wrapper script
cat > leetcode-fsrs-wrapper << 'EOF'
#!/bin/bash
# Wrapper script for leetcode-fsrs-cli
# This allows running without Python dependencies

# Find Python interpreter
PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null)

if [ -z "$PYTHON" ]; then
    echo "Error: Python interpreter not found"
    exit 1
fi

# Run the actual Python script
"$PYTHON" -c "
import sys
import os

# Add package path
package_path = os.path.join(os.path.dirname(__file__), 'leetcode_fsrs_cli')
sys.path.insert(0, package_path)

# Import and run CLI
from leetcode_fsrs_cli.cli import cli

if __name__ == '__main__':
    cli()
" "$@"
EOF

chmod +x leetcode-fsrs-wrapper

# Create binary package name
BINARY_NAME="leetcode-fsrs-cli-1.0.0-1-x86_64"

# Create package directory structure
mkdir -p pkg-bin/usr/bin
mkdir -p pkg-bin/usr/share/leetcode-fsrs-cli/data
mkdir -p pkg-bin/usr/share/licenses/leetcode-fsrs-cli-bin
mkdir -p pkg-bin/usr/share/doc/leetcode-fsrs-cli-bin

# Copy files
cp leetcode-fsrs-wrapper pkg-bin/usr/bin/leetcode-fsrs
cp -r leetcode_fsrs_cli pkg-bin/usr/bin/
cp LICENSE pkg-bin/usr/share/licenses/leetcode-fsrs-cli-bin/
cp README.md pkg-bin/usr/share/doc/leetcode-fsrs-cli-bin/

# Create default config
echo '{}' > pkg-bin/usr/share/leetcode-fsrs-cli/data/config.json

# Create package info
cat > pkg-bin/.PKGINFO << EOF
pkgname = leetcode-fsrs-cli-bin
pkgver = 1.0.0-1
pkgdesc = A CLI tool for LeetCode practice using FSRS spaced repetition algorithm (binary version)
url = https://github.com/SaintFore/LeetCodeCLI
builddate = $(date +%s)
packager = SaintFore <saintfore@example.com>
size = $(du -sb pkg-bin | cut -f1)
arch = x86_64
license = MIT
depend = python
EOF

# Create package
cd pkg-bin
bsdtar -czf ../$BINARY_NAME.pkg.tar.xz .
cd ..

# Clean up
rm -rf pkg-bin leetcode-fsrs-wrapper

echo "Simple binary package created: $BINARY_NAME.pkg.tar.xst"