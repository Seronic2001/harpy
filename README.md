# Harpy 🦅

[![CI](https://github.com/seronic/harpy/actions/workflows/ci.yml/badge.svg)](https://github.com/seronic/harpy/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![PyPI version](https://img.shields.io/badge/pypi-0.1.0-orange.svg)](https://pypi.org/project/harpy-cp/)

> **The AI-assisted Competitive Programming & Technical Interview Toolkit.**
> Turn raw problem statements or whiteboard screenshots into LeetCode-style templates, generate guaranteed test suites with a reference Python oracle, and sync directly with CPH and fast local test runners.

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
- 🤖 **Native Model Context Protocol (MCP) & AI Skill**:
  - Drop a screenshot of an exam question, contest problem, or whiteboard into chat.
  - The AI assistant formulates the problem, generates tests, sets up your starter template, and tests your code.
- 🔇 **Distraction-Free Coding**: Auto-configures `.tabignore` to silence intrusive inline AI autocomplete while you code.

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

# Enable fast tab-completion for problem slugs
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
This scaffolds a `problems/` directory and creates `.tabignore` so inline ghost AI suggestions don't distract you while solving problems.

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
Push problem metadata and test cases to your active CPH listener in VS Code / Antigravity:
```bash
harpy push problems/maximum-subarray-sum
```

---

## 🤖 AI Assistant Integration

Harpy exposes tools over the **Model Context Protocol (MCP)**:
- `harpy_setup_problem`: Formulate problem specifications and starter code.
- `harpy_oracle_generate_tests`: Run reference Python code to generate verified test cases.
- `harpy_sync_cph`: Push tests to CPH over HTTP and `.cph/` files.
- `harpy_test_solution`: Run solution and report CE/WA/TLE/RTE with execution times.

### Antigravity IDE
Run `harpy setup-ai` and Antigravity will automatically register the MCP server and install the `harpy-cp` skill globally.

### Cursor
Add to `.cursor/mcp.json`:
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

### Claude Desktop
Add to `claude_desktop_config.json`:
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
python -m build
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
