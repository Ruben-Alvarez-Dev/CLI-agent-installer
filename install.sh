#!/bin/bash
# install.sh — Installer for CLI-agent-installer itself
# Usage: curl -fsSL https://raw.githubusercontent.com/Ruben-Alvarez-Dev/CLI-agent-installer/main/install.sh | bash

set -euo pipefail

# Configuration
REPO="Ruben-Alvarez-Dev/CLI-agent-installer"
INSTALL_DIR="${1:-$HOME/.local/share/cli-agent-installer}"
VENV_DIR="$INSTALL_DIR/.venv"
BIN_DIR="${2:-$HOME/.local/bin}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   CLI-agent-installer — Installer                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
PYTHON="python3"
if ! command -v $PYTHON &>/dev/null; then
    echo "✗ Python 3.12+ required"
    exit 1
fi

PYVER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Python $PYVER found"

# Download source
echo ""
echo "→ Downloading source..."
TMPDIR=$(mktemp -d -t installer.XXXXXX)
trap "rm -rf $TMPDIR" EXIT

if ! curl -fsSL "https://github.com/${REPO}/archive/refs/heads/main.tar.gz" -o "$TMPDIR/src.tar.gz"; then
    echo "✗ Download failed"
    exit 1
fi

mkdir -p "$TMPDIR/repo"
tar -xzf "$TMPDIR/src.tar.gz" -C "$TMPDIR/repo" --strip-components=1
echo "✓ Source downloaded"

# Create install directory
echo ""
echo "→ Installing to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -a "$TMPDIR/repo/." "$INSTALL_DIR/"
echo "✓ Files copied"

# Create venv
echo ""
echo "→ Creating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON -m venv "$VENV_DIR"
fi
echo "✓ Virtual environment created"

# Install package
echo ""
echo "→ Installing package..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q 2>/dev/null
pip install -e "$INSTALL_DIR" -q 2>/dev/null
echo "✓ Package installed"

# Create symlink to bin
echo ""
echo "→ Creating symlink..."
mkdir -p "$BIN_DIR"
ln -sf "$VENV_DIR/bin/installer" "$BIN_DIR/installer" 2>/dev/null || true

# Add to PATH if needed
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "⚠️  $BIN_DIR is not in your PATH"
    echo "   Add this to your shell profile (~/.bashrc, ~/.zshrc):"
    echo "   export PATH=\"\$PATH:$BIN_DIR\""
fi

# Verify
echo ""
echo "→ Verifying installation..."
if $VENV_DIR/bin/installer version /dev/null &>/dev/null; then
    echo "✓ Installation verified"
else
    echo "⚠️  Verification failed"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   ✅ Installation complete                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Usage:"
echo "  installer init ~/my-project --repo \"owner/repo\""
echo "  installer run ~/my-project"
echo "  installer check ~/my-project"
echo ""
echo "Docs: https://github.com/${REPO}"
