#!/usr/bin/env bash
set -e

# --- Colors & Styling ---
BOLD="\033[1m"
DIM="\033[2m"
RESET="\033[0m"

C_BLUE="\033[38;5;39m"
C_CYAN="\033[38;5;45m"
C_GREEN="\033[38;5;82m"
C_YELLOW="\033[38;5;220m"
C_RED="\033[38;5;196m"

print_banner() {
    printf "\n"
    printf "${C_BLUE}    __  __                            ${RESET}\n"
    printf "${C_CYAN}   / / / /___ _________  __  __       ${RESET}\n"
    printf "${C_CYAN}  / /_/ / __ \`/ ___/ __ \/ / / /  🦅   ${RESET}\n"
    printf "${C_BLUE} / __  / /_/ / /  / /_/ / /_/ /       ${RESET}\n"
    printf "${C_BLUE}/_/ /_/\__,_/_/  / .___/\__, /        ${RESET}\n"
    printf "                /_/    /____/         \n"
    printf "  ${DIM}Harpy Uninstaller${RESET}\n"
    printf "  ${DIM}────────────────────────────────────────────────────────${RESET}\n\n"
}

main() {
    print_banner

    INSTALL_BIN="$HOME/.local/bin/harpy"
    GEMINI_SKILL="$HOME/.gemini/config/skills/harpy-cp"
    GEMINI_MCP="$HOME/.gemini/config/mcp_config.json"

    # 1. Remove binary
    if [ -f "$INSTALL_BIN" ]; then
        rm -f "$INSTALL_BIN"
        printf "  ${C_GREEN}✔${RESET} Removed binary: ${BOLD}%s${RESET}\n" "$INSTALL_BIN"
    else
        printf "  ${DIM}• Binary not found at %s (skipped)${RESET}\n" "$INSTALL_BIN"
    fi

    # 2. Remove Antigravity skill
    if [ -d "$GEMINI_SKILL" ]; then
        rm -rf "$GEMINI_SKILL"
        printf "  ${C_GREEN}✔${RESET} Removed AI skill: ${BOLD}%s${RESET}\n" "$GEMINI_SKILL"
    fi

    # 3. Clean MCP config if present
    if [ -f "$GEMINI_MCP" ]; then
        if command -v python3 >/dev/null 2>&1; then
            python3 -c "
import json, sys
p = '$GEMINI_MCP'
try:
    with open(p, 'r') as f: data = json.load(f)
    if 'mcpServers' in data and 'harpy' in data['mcpServers']:
        del data['mcpServers']['harpy']
        with open(p, 'w') as f: json.dump(data, f, indent=2)
        print('  \033[38;5;82m✔\033[0m Removed harpy from MCP config: \033[1m' + p + '\033[0m')
except Exception: pass
"
        fi
    fi

    # 4. Summary Box
    printf "\n"
    printf "  ${C_BLUE}╭──────────────────────────────────────────────────────────────╮${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  ${C_YELLOW}👋 Harpy has been completely uninstalled.${RESET}                    ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}├──────────────────────────────────────────────────────────────┤${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  All standalone binaries, skills, and MCP configurations     ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  have been removed from your system.                         ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}                                                              ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  ${DIM}To reinstall anytime, run:${RESET}                                  ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}│${RESET}  ${C_CYAN}curl -fsSL https://raw.githubusercontent.com/... | bash${RESET}    ${C_BLUE}│${RESET}\n"
    printf "  ${C_BLUE}╰──────────────────────────────────────────────────────────────╯${RESET}\n\n"
}

main "$@"
