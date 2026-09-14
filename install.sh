#!/usr/bin/env bash
set -e

# --- Colors & Styling ---
BOLD="\033[1m"
DIM="\033[2m"
RESET="\033[0m"

C_BLUE="\033[38;5;39m"
C_CYAN="\033[38;5;45m"
C_BRIGHT_CYAN="\033[38;5;51m"
C_GREEN="\033[38;5;82m"
C_YELLOW="\033[38;5;220m"
C_PURPLE="\033[38;5;141m"
C_RED="\033[38;5;196m"

# --- Cursor Cleanup Trap ---
trap 'printf "\033[?25h" 2>/dev/null || true' EXIT INT TERM

# --- Animated Banner ---
clear_screen() {
    printf "\033[H\033[2J" 2>/dev/null || true
}

print_banner() {
    printf "\n"
    printf "${C_BLUE}    __  __                            ${RESET}\n"
    printf "${C_CYAN}   / / / /___ _________  __  __       ${RESET}\n"
    printf "${C_BRIGHT_CYAN}  / /_/ / __ \`/ ___/ __ \/ / / /  🦅   ${RESET}\n"
    printf "${C_CYAN} / __  / /_/ / /  / /_/ / /_/ /       ${RESET}\n"
    printf "${C_BLUE}/_/ /_/\__,_/_/  / .___/\__, /        ${RESET}\n"
    printf "${C_PURPLE}                /_/    /____/         ${RESET}\n"
    printf "  ${DIM}⚡ Fast Competitive Programming & Interview Prep Toolkit${RESET}\n"
    printf "  ${DIM}────────────────────────────────────────────────────────${RESET}\n\n"
}

# --- Spinner Animation ---
spin() {
    local pid=$1
    local msg=$2
    local spin_chars=("⠋" "⠙" "⠹" "⠸" "⠼" "⠴" "⠦" "⠧" "⠇" "⠏")
    local i=0

    # Hide cursor
    printf "\033[?25l"

    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${C_CYAN}%s${RESET} %s..." "${spin_chars[i]}" "$msg"
        i=$(( (i + 1) % 10 ))
        sleep 0.08
    done

    # Wait for process to collect exit code
    wait "$pid"
    local exit_code=$?

    # Restore cursor
    printf "\033[?25h"

    if [ "$exit_code" -eq 0 ]; then
        printf "\r\033[K  ${C_GREEN}✔${RESET} %s\n" "$msg"
    else
        printf "\r\033[K  ${C_RED}✖${RESET} %s (failed)\n" "$msg"
        exit "$exit_code"
    fi
}

main() {
    print_banner

    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"

    # 1. Detect OS & Architecture
    OS="$(uname -s)"
    ARCH="$(uname -m)"

    if [ "$OS" = "Linux" ]; then
        if [ "$ARCH" = "x86_64" ]; then
            URL="https://github.com/Seronic2001/harpy/releases/latest/download/harpy-linux-x86_64"
            PLATFORM="Linux (x86_64)"
        else
            printf "  ${C_RED}✖${RESET} Unsupported Linux architecture: %s (only x86_64 currently supported for binaries)\n" "$ARCH"
            printf "    Tip: You can install via pip: ${BOLD}pip install harpy-cp${RESET}\n"
            exit 1
        fi
    elif [ "$OS" = "Darwin" ]; then
        URL="https://github.com/Seronic2001/harpy/releases/latest/download/harpy-macos-arm64"
        PLATFORM="macOS (Apple Silicon arm64)"
    else
        printf "  ${C_RED}✖${RESET} Unsupported operating system: %s\n" "$OS"
        exit 1
    fi

    printf "  ${C_GREEN}✔${RESET} Detected platform: ${BOLD}%s${RESET}\n" "$PLATFORM"

    # 2. Download Binary with Animated Spinner
    TARGET_BIN="$INSTALL_DIR/harpy"
    TMP_BIN="$INSTALL_DIR/.harpy_download.$$"

    curl -sSL "$URL" -o "$TMP_BIN" &
    CURL_PID=$!
    spin "$CURL_PID" "Downloading Harpy standalone binary"

    mv "$TMP_BIN" "$TARGET_BIN"
    chmod +x "$TARGET_BIN"

    # 3. Verify Binary Execution
    VERSION=$("$TARGET_BIN" --version 2>/dev/null || echo "harpy")
    printf "  ${C_GREEN}✔${RESET} Verified binary: ${BOLD}%s${RESET}\n" "$VERSION"

    # 4. Check & Configure PATH
    PATH_UPDATED=0
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        SHELL_NAME="$(basename "${SHELL:-bash}")"
        if [ "$SHELL_NAME" = "zsh" ]; then
            PROFILE="$HOME/.zshrc"
        elif [ "$SHELL_NAME" = "fish" ]; then
            PROFILE="$HOME/.config/fish/config.fish"
        else
            PROFILE="$HOME/.bashrc"
        fi

        if [ "$SHELL_NAME" = "fish" ]; then
            echo "fish_add_path $INSTALL_DIR" >> "$PROFILE"
        else
            echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$PROFILE"
        fi

        printf "  ${C_GREEN}✔${RESET} Added ${C_CYAN}%s${RESET} to ${BOLD}%s${RESET}\n" "$INSTALL_DIR" "$PROFILE"
        PATH_UPDATED=1
    else
        printf "  ${C_GREEN}✔${RESET} Shell PATH: ${DIM}%s is already in PATH${RESET}\n" "$INSTALL_DIR"
    fi

    # 5. Success Card Box
    printf "\n"
    printf "  ${C_BLUE}╭──────────────────────────────────────────────────────────────╮${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  ${C_GREEN}✨ Harpy installed successfully!${RESET}                            ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}├──────────────────────────────────────────────────────────────┤${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  • ${BOLD}Executable:${RESET}  %-44s ${C_BLUE}│${RESET}\n" "$TARGET_BIN"
    printf "  ${C_BLUE}│${RESET}  • ${BOLD}Version:${RESET}     %-44s ${C_BLUE}│${RESET}\n" "$VERSION"
    printf "  ${C_BLUE}│${RESET}                                                              ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  ${BOLD}Next Steps:${RESET}                                                 ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}    ${C_CYAN}1.${RESET} Auto-configure AI & MCP:   ${C_GREEN}harpy setup-ai${RESET}              ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}    ${C_CYAN}2.${RESET} Enable tab completions:    ${C_GREEN}harpy completion install${RESET}    ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}    ${C_CYAN}3.${RESET} Start practicing:          ${C_GREEN}harpy init${RESET}                  ${C_BLUE}│${RESET}\n"
    if [ "$PATH_UPDATED" -eq 1 ]; then
    printf "  ${C_BLUE}│${RESET}                                                              ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  ${C_YELLOW}⚠ Reload terminal or run:${RESET}   ${BOLD}source %-24s${RESET} ${C_BLUE}│${RESET}\n" "$PROFILE"
    fi
    printf "  ${C_BLUE}╰──────────────────────────────────────────────────────────────╯${RESET}\n\n"
}

main "$@"
