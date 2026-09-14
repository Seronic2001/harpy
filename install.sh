#!/usr/bin/env bash
set -e

INSTALL_DIR="$HOME/.local/bin"
mkdir -p "$INSTALL_DIR"

OS="$(uname -s)"
ARCH="$(uname -m)"

if [ "$OS" = "Linux" ]; then
    URL="https://github.com/Seronic2001/harpy/releases/latest/download/harpy-linux-x86_64"
elif [ "$OS" = "Darwin" ]; then
    URL="https://github.com/Seronic2001/harpy/releases/latest/download/harpy-macos-arm64"
else
    echo "Error: Unsupported operating system $OS"
    exit 1
fi

echo "🦅 Downloading Harpy for $OS..."
curl -sSL "$URL" -o "$INSTALL_DIR/harpy"
chmod +x "$INSTALL_DIR/harpy"

# Add to PATH if needed
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    SHELL_NAME="$(basename "${SHELL:-bash}")"
    if [ "$SHELL_NAME" = "zsh" ]; then
        PROFILE="$HOME/.zshrc"
    else
        PROFILE="$HOME/.bashrc"
    fi
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$PROFILE"
    echo "✔ Added $INSTALL_DIR to $PROFILE"
    export PATH="$INSTALL_DIR:$PATH"
fi

echo "✨ Harpy installed successfully to $INSTALL_DIR/harpy!"
echo "Run 'harpy setup-ai' to get started."
