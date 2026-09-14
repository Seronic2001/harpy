# Harpy 🦅

[![CI](https://github.com/Seronic2001/harpy/actions/workflows/ci.yml/badge.svg)](https://github.com/Seronic2001/harpy/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/harpy-cp.svg)](https://pypi.org/project/harpy-cp/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/harpy-cp.svg)](https://pypi.org/project/harpy-cp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)

> **A CLI toolkit and Model Context Protocol (MCP) server for competitive programming.**
> Converts problem statements into decoupled C++ templates, runs brute-force differential testing to eliminate AI test-case hallucination, and synchronizes test cases directly with CPH and local compilers.

---

## ✨ Features

- 📑 **Decoupled Code Templates**: Converts problem descriptions into clean, typed `solve(...)` function templates with fast I/O in `main()`, separating I/O parsing from core algorithmic logic.
- ⚡ **Instant Scaffolding & Background Test Synthesis**: Scaffolds starter code, problem specifications, and CPH files in `<200ms`, while synthesizing and verifying edge/stress test cases in the background via detached processes (`--async`).
- 🎯 **Brute-Force Differential Testing & Batch Oracle**: Eliminates AI test-case hallucination. Runs a simple brute-force Python script locally across edge cases, boundary conditions ($N=0, 1$, negative numbers), and randomized stress tests to generate 100% verified expected outputs in a single batched process.
- ⚡ **Competitive Programming Helper (CPH) Sync**:
  - Live HTTP dispatch to VS Code / Antigravity CPH extension on port `27121`.
  - Generates native `.cph/` `.prob` files directly for offline use.
- 🧪 **Fast Local Test Runner (`harpy test`)**:
  - Compiles C++ (`g++ -O3 -std=c++17`), Python, and Java.
  - Formats results with color-coded tables, execution time, and side-by-side failure diffs.
- 🤖 **Universal Model Context Protocol (MCP) Server**:
  - Exposes deterministic tools (`setup_problem`, `oracle_generate_tests`, `sync_cph`, `test_solution`) for coding agents in **VS Code**, **Antigravity**, **Cursor**, **Windsurf**, **Claude Desktop**, and **Zed**.
- 🔇 **Distraction-Free Workspace**: Auto-configures `.tabignore` to silence intrusive inline AI autocomplete while you code algorithms.

---

## 🚀 Quickstart

### 1. Installation

#### Option A: Standalone Binary (Recommended — Zero Python setup needed)

Harpy ships as a self-contained executable with no Python or virtual environment dependencies:

- **Linux (x86_64)**:
  ```bash
  mkdir -p ~/.local/bin
  curl -sSL https://github.com/Seronic2001/harpy/releases/latest/download/harpy-linux-x86_64 -o ~/.local/bin/harpy
  chmod +x ~/.local/bin/harpy
  ```

- **macOS (Apple Silicon M1/M2/M3/M4)**:
  ```bash
  mkdir -p ~/.local/bin
  curl -sSL https://github.com/Seronic2001/harpy/releases/latest/download/harpy-macos-arm64 -o ~/.local/bin/harpy
  chmod +x ~/.local/bin/harpy
  ```

- **Windows**:
  Download `harpy-windows-x86_64.exe` from the [Latest Release](https://github.com/Seronic2001/harpy/releases/latest), rename to `harpy.exe`, and add to your `PATH`.

> *Tip: Ensure `~/.local/bin` is in your `PATH` (e.g., `export PATH="$HOME/.local/bin:$PATH"`).*

#### Option B: Via `pip` or `pipx`

```bash
# Recommended: install globally via pipx (auto-configures PATH)
pipx install harpy-cp

# Or via standard pip
pip install harpy-cp
```

> **Windows Tip**: If `harpy` is not found after `pip install`, ensure your user Scripts directory (e.g. `%APPDATA%\Python\Python312\Scripts`) is added to your `PATH`, or use `pipx` which handles this automatically.

To update to the latest version:
```bash
pipx upgrade harpy-cp
# Or with pip:
pip install --upgrade harpy-cp
```

Or install the latest development commit directly from GitHub:
```bash
pipx install --force git+https://github.com/Seronic2001/harpy.git
```

### 2. Configure AI & Shell Completion (1-Command Setup)

```bash
# Auto-installs Antigravity skill & registers Harpy MCP server
harpy setup-ai

# Enable fast tab-completion for problem slugs and solutions
harpy completion install
```

---

## 💻 CLI Usage

### Initialize a DSA Workspace
In any folder where you want to practice problems (e.g. `~/dsa-prep`):
```bash
mkdir -p ~/dsa-prep && cd ~/dsa-prep
harpy init
```
**What `harpy init` sets up:**
- Scaffolds a `problems/` directory.
- Configures `.tabignore` and `.antigravityignore` so inline ghost AI suggestions don't distract you while solving problems.

### Create & Scaffold Problems (1-Command Setup)
Create a categorized problem workspace, run reference oracle test verification, and sync to CPH in a single command:
```bash
# Instant scaffolding (<0.2s) with detached background test synthesis
harpy create -s spec.json --async

# Or wait synchronously for test generation and verification
harpy create -s spec.json --sync

# Or pipe specification directly via stdin
cat spec.json | harpy create - --async

# Quick flag-based setup
harpy create --title "Two Sum" --category "sorting-and-searching" --difficulty "Easy"
```

### Synthesize Additional Tests / Stress Test
```bash
# Run algorithmic test generator and verify with reference oracle
harpy generate-tests problems/two-sum

# Or run in the background with alias
harpy stress problems/two-sum -b
```

### Test Solutions Locally
```bash
# Auto-resolves problem slugs and files inside problems/
harpy test lexicographically-minimal-walk

# Or direct file paths
harpy test problems/two-sum/solution.cpp
```
Output:
```text
⚡ Harpy Test Runner: Testing solution.cpp (cpp)
            Test Results             
┏━━━━━━━━┳━━━━━━━━┳━━━━━━━━┳━━━━━━━━┓
┃ Case # ┃  Type  ┃ Status ┃   Time ┃
┡━━━━━━━━╇━━━━━━━━╇━━━━━━━━╇━━━━━━━━┩
│   01   │ sample │ ✔ PASS │ 2.7 ms │
│   02   │ sample │ ✔ PASS │ 3.0 ms │
│   03   │ edge   │ ✔ PASS │ 2.9 ms │
│   04   │ stress │ ✔ PASS │ 5.1 ms │
└────────┴────────┴────────┴────────┘
✨ All 4 test cases passed!
```

### Push to CPH Extension
Push problem metadata and test cases to your active CPH listener in VS Code or Antigravity:
```bash
harpy push problems/maximum-subarray-sum
```

---

## 🛠️ IDE Setup Guide

Harpy connects to any editor via two open standards:
1. **Model Context Protocol (MCP)**: Lets AI assistants formulate problems, run brute-force differential testing, and execute test runners.
2. **CPH Protocol & `.cph/` Files**: Integrates directly with the Competitive Programming Helper extension.

### IDE Compatibility Matrix

| IDE / Editor | AI Assistant (MCP) | CPH GUI Test Runner | Integrated CLI | Autocomplete Mute (`.tabignore`) |
|---|:---:|:---:|:---:|:---:|
| **VS Code** | ✔ (Roo Code / Cline / Copilot) | ✔ (CPH Extension) | ✔ | ✔ |
| **Google Antigravity** | ✔ (Native 1-Command) | ✔ (CPH Extension) | ✔ | ✔ |
| **Cursor** | ✔ (Native Composer MCP) | ✔ (CPH via Open VSX/Marketplace) | ✔ | ✔ |
| **Windsurf** | ✔ (Native Cascade MCP) | ✔ (CPH Extension) | ✔ | ✔ |
| **Zed** | ✔ (Context Servers) | — (Uses CLI `harpy test`) | ✔ | ✔ |
| **Claude Desktop** | ✔ (Native MCP) | — (Uses CLI `harpy test`) | ✔ | ✔ |
| **Neovim / JetBrains** | — (Terminal / LLM plugins) | ✔ (Competitive Companion / CLI) | ✔ | ✔ |

---

### 1. VS Code

#### CPH Extension Setup
1. Install the **Competitive Programming Helper (cph)** extension from the VS Code Marketplace:
   `ext install divyanshuaggarwal.competitive-programming-helper`
2. When you push a problem using `harpy push <slug>`, it opens directly in the CPH sidebar with all test cases preloaded.
3. Offline support: Harpy automatically creates `.cph/.<slug>.cpp_<hash>.prob` files so tests load even without an active network connection.

#### AI Assistant (Roo Code / Cline / GitHub Copilot Chat)
Add Harpy to your MCP settings file (e.g. `cline_mcp_settings.json` or `.vscode/mcp.json`):
```json
{
  "mcpServers": {
    "harpy": {
      "command": "python3",
      "args": ["-m", "harpy.mcp_server"]
    }
  }
}
```

---

### 2. Google Antigravity IDE

Harpy has first-class native integration with Antigravity:
1. Run the one-command installer:
   ```bash
   harpy setup-ai
   ```
   This automatically:
   - Registers the MCP server in `~/.gemini/config/mcp_config.json`.
   - Installs the multimodal `harpy-cp` skill globally in `~/.gemini/config/skills/harpy-cp/SKILL.md`.
2. Open any folder (`harpy init`), drop a screenshot of a problem or contest into chat, and say:
   > *"Set this problem up."*
3. Antigravity automatically:
   - Formulates `problem.md`.
   - Writes `<slug>.cpp` with typed LeetCode `solve(...)` signature.
   - Runs the brute-force Python script to verify sample, edge, and stress cases.
   - Syncs with CPH and gives you a clickable file link to your code.

---

### 3. Cursor

1. Open **Cursor Settings** (`Cmd+,` or `Ctrl+,`) → **Features** → **MCP**.
2. Click **+ Add New MCP Server**:
   - **Name**: `harpy`
   - **Type**: `command`
   - **Command**: `python3 -m harpy.mcp_server`
3. Alternatively, create a `.cursor/mcp.json` file in your workspace:
   ```json
   {
     "mcpServers": {
       "harpy": {
         "command": "python3",
         "args": ["-m", "harpy.mcp_server"]
       }
     }
   }
   ```
4. Add to your `.cursorrules` (optional, for optimal prompt alignment):
   ```markdown
   When asked to set up a competitive programming or algorithm problem:
   1. Use the `harpy_setup_problem` tool.
   2. Leave the body of `solve(...)` empty for the user with pre-filled typed parameters from `main()`.
   3. Write a brute-force Python script and use `harpy_oracle_generate_tests`.
   4. Sync to CPH using `harpy_sync_cph`.
   ```

---

### 4. Windsurf (Codeium)

Windsurf supports MCP via Cascade:
1. Open or create `~/.codeium/windsurf/mcp_config.json` (or workspace `.windsurf/mcp.json`):
   ```json
   {
     "mcpServers": {
       "harpy": {
         "command": "python3",
         "args": ["-m", "harpy.mcp_server"]
       }
     }
   }
   ```
2. Restart Cascade. Harpy tools will appear with a green indicator in the tools list.

---

### 5. Claude Desktop

In `~/.config/Claude/claude_desktop_config.json` (Linux/macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):
```json
{
  "mcpServers": {
    "harpy": {
      "command": "python3",
      "args": ["-m", "harpy.mcp_server"]
    }
  }
}
```

---

### 6. Zed Editor

Zed supports context servers via `~/.config/zed/settings.json`:
```json
{
  "context_servers": {
    "harpy": {
      "command": {
        "path": "python3",
        "args": ["-m", "harpy.mcp_server"]
      }
    }
  }
}
```

---

### 7. Neovim & Terminal-First Workflow

For Neovim, tmux, and terminal-first users:
1. **Interactive Testing**: Run `harpy test <slug>` in a side tmux pane, floating terminal, or Neovim terminal (`:terminal harpy test <slug>`).
2. **Watch Mode**: Use with `entr` or `nodemon` to automatically test whenever you save your solution:
   ```bash
   ls problems/<slug>/*.cpp | entr -c harpy test <slug>
   ```
3. **Tab Completion**: Auto-completes subcommands, problem slugs, and solution files:
   ```bash
   harpy test lexi<TAB>
   ```

---

## 📁 Problem Structure

Harpy automatically organizes problems by algorithmic topic into standard CSES category subfolders:
```text
problems/<category>/<slug>/
├── problem.md         # LeetCode-style specification with LaTeX constraints
├── problem.json       # Structured problem metadata & test cases
├── <slug>.cpp         # Starter template with pre-filled typed solve(...)
├── tests/
│   ├── in_01.txt      # Input for test case 1
│   ├── out_01.txt     # Verified expected output for test case 1
│   └── ...
└── .cph/
    └── .<slug>.cpp_<hash>.prob  # Native CPH offline test file
```

Supported CSES categories include `dynamic-programming`, `graph-algorithms`, `tree-algorithms`, `sorting-and-searching`, `greedy-algorithms`, `range-queries`, `mathematics`, `string-algorithms`, `geometry`, `bit-manipulation`, `introductory-problems`, and `advanced-techniques`.

---

## 🧪 Development & Testing

Run unit tests:
```bash
pytest -v
```

Build standalone package:
```bash
python3 -m build
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
