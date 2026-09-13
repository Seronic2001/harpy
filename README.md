# Harpy 🦅

**Harpy** is an AI-assisted competitive programming and technical interview prep toolkit. It transforms unstructured algorithm problem descriptions (from images, whiteboard photos, screenshots, or messy text) into standardized **LeetCode-style specifications**, generates **guaranteed test cases via a reference Python oracle**, and connects directly with **CPH (Competitive Programming Helper)** and local runners.

---

## Features

- 📑 **LeetCode-Style Problem Formulation**: Converts raw text or images into structured Markdown complete with LaTeX constraints (`$1 \le N \le 10^5$`), time/memory limits, formal I/O formats, and step-by-step examples.
- 🎯 **Oracle-Verified Test Cases**: Generates edge cases ($N=0, 1$, negative numbers, boundary limits, identical elements) and large stress tests. An automated Python reference solver executes locally to compute guaranteed, hallucination-free outputs.
- ⚡ **Seamless CPH Integration**:
  - **Live Dispatch**: Sends problems to VS Code via the Competitive Companion HTTP protocol (port `27121`).
  - **Direct `.cph/` Files**: Generates `.cph/.solution.cpp_<hash>.prob` directly in the problem folder, so tests load immediately even when offline.
- 🧪 **Built-in Local Test Runner**:
  - Compiles and runs C++ (`g++ -O3 -std=c++17`), Python, and Java.
  - Measures execution time and memory.
  - Formats results with color-coded tables and side-by-side failure diffs.
- 🤖 **Model Context Protocol (MCP) Server & Antigravity Skill**:
  - Allows you to drop an image or paste a problem into chat and say *"Set up this problem in CPH and generate test cases"*.

---

## Directory Structure

When a problem is created, Harpy organizes it as:
```text
problems/<problem-slug>/
├── problem.md         # LeetCode-style formatted problem
├── problem.json       # Structured problem metadata & test suite
├── solution.cpp       # Starter code template (or solution.py)
├── tests/
│   ├── in_01.txt      # Input for case 1
│   ├── out_01.txt     # Verified expected output
│   └── ...
└── .cph/
    └── .solution.cpp_<hash>.prob  # Native CPH test file
```

---

## Quickstart

### 1. Installation

```bash
git clone https://github.com/seronic/harpy.git
cd harpy
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Testing a Solution Locally

Run your solution against all generated test cases:
```bash
harpy test problems/maximum-subarray-sum/solution.cpp
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
│   03   │ sample │ ✔ PASS │ 2.9 ms │
│   04   │ sample │ ✔ PASS │ 2.8 ms │
└────────┴────────┴────────┴────────┘
✨ All 4 test cases passed!
```

### 3. Pushing to CPH in VS Code

If you have the **Competitive Programming Helper (CPH)** extension open in VS Code, push any problem directly into your editor:
```bash
harpy push problems/maximum-subarray-sum
```

---

## Chat & MCP Workflow

Harpy includes an MCP server configured in `~/.gemini/config/mcp_config.json` and an Antigravity skill in `.agents/skills/harpy-cp/SKILL.md`.

Simply upload an image (e.g., photo of an exam question or whiteboard problem) or paste problem text into the chat, and say:
> *"Set this up in C++ with test cases and sync to CPH."*

Harpy will:
1. Formulate the problem statement.
2. Run a reference oracle to compute authoritative expected outputs for samples & edge cases.
3. Scaffold `problem.md` and `solution.cpp`.
4. Sync to CPH on port `27121` and write `.cph/`.
5. Run tests with `harpy test` when you write your solution.
