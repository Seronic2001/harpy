# Harpy 🦅

[![CI](https://github.com/seronic/harpy/actions/workflows/ci.yml/badge.svg)](https://github.com/seronic/harpy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![PyPI version](https://img.shields.io/badge/pypi-0.1.0-orange.svg)](https://pypi.org/project/harpy-cp/)

> **The AI-assisted Competitive Programming & Technical Interview Toolkit.**
> Turn raw problem statements or whiteboard screenshots into LeetCode-style templates, generate guaranteed test suites with a reference Python oracle, and sync directly with CPH and fast local test runners across any IDE.

---

## ✨ Features

- 📑 **LeetCode-Style Starter Code**: Converts problem descriptions into clean, typed `solve(...)` function templates with fast I/O in `main()`. You focus purely on the algorithm.
- 🎯 **Oracle-Verified Test Cases**: Never guess edge cases. A local reference Python oracle runs locally to generate authoritative, verified expected outputs for samples, boundary conditions, and stress tests.
- ⚡ **Competitive Programming Helper (CPH) Sync**:
  - Live HTTP dispatch to VS Code / Antigravity CPH extension on port `27121`.
  - Generates native `.cph/` `.prob` files directly for offline use.
- 🧪 **Fast Local Test Runner (`harpy test`)**:
  - Compiles C++ (`g++ -O3 -std=c++17`), Python, and Java.
  - Formats results with color-coded tables, execution time, and side-by-side failure diffs.
- 🤖 **Universal Model Context Protocol (MCP) & AI Assistant Support**:
  - Works natively with **VS Code**, **Antigravity**, **Cursor**, **Windsurf**, **Claude Desktop**, **Zed**, and terminal-first workflows.
- 🔇 **Distraction-Free Coding**: Auto-configures `.tabignore` to silence intrusive inline AI autocomplete while you code algorithms.

---

## 🚀 Quickstart

### 1. Installation

Install via `pip` or `pipx`:

```bash
# Recommended: install globally with pipx
pipx install harpy-cp

# Or standard pip
pip install harpy-cp
```

Or install from source:
```bash
git clone https://github.com/seronic/harpy.git
cd harpy
pip install -e .
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
1. **Model Context Protocol (MCP)**: Lets AI assistants formulate problems, run the test oracle, and test code.
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
   - Runs the reference Python oracle to verify sample, edge, and stress cases.
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
   3. Write a reference Python oracle and use `harpy_oracle_generate_tests`.
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

When a problem is created, Harpy structures it cleanly:
```text
problems/<slug>/
├── problem.md         # LeetCode-style specification with LaTeX constraints
├── problem.json       # Structured problem metadata & test cases
├── <slug>.cpp         # Starter template with pre-filled typed solve(...)
├── tests/
│   ├── in_01.txt      # Input for test case 1
│   ├── out_01.txt     # Oracle-verified output for test case 1
│   └── ...
└── .cph/
    └── .<slug>.cpp_<hash>.prob  # Native CPH offline test file
```

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
