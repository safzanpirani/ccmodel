#!/bin/sh
# One-liner installer for ccmodel.
# Usage: curl -fsSL https://raw.githubusercontent.com/safzanpirani/ccmodel/main/install.sh | sh

set -e

REPO="safzanpirani/ccmodel"
BRANCH="main"

if [ -n "$DESTDIR" ]; then
    INSTALL_DIR="$DESTDIR"
elif [ -d "$HOME/.local/bin" ]; then
    INSTALL_DIR="$HOME/.local/bin"
else
    INSTALL_DIR="/usr/local/bin"
fi

TARGET="$INSTALL_DIR/ccmodel"
URL="https://raw.githubusercontent.com/$REPO/$BRANCH/bin/ccmodel"

echo "Installing ccmodel to $TARGET ..."
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$URL" -o "$TARGET"
else
    wget -q "$URL" -O "$TARGET"
fi
chmod +x "$TARGET"

if [ "$INSTALL_DIR" != "$HOME/.local/bin" ] && [ ! -w "$INSTALL_DIR" ]; then
    echo "Need write access to $INSTALL_DIR. Re-running with sudo ..."
    sudo curl -fsSL "$URL" -o "$TARGET" || sudo wget -q "$URL" -O "$TARGET"
    sudo chmod +x "$TARGET"
fi

echo "ccmodel installed. Run 'ccmodel ls' to see profiles."
