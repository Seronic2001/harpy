---
name: harpy-cp
description: Formulates algorithm problems from uploaded images or raw text into LeetCode-style markdown specifications, generates verified test cases using a Python reference oracle, creates a starter <problem_slug>.cpp (or .py) file with an empty solve(...) function with prefilled parameters for the user to implement, syncs with CPH, and tests solutions.
---

# Harpy Competitive Programming Workflow

Follow this procedure whenever the user:
- Uploads an image, screenshot, whiteboard photo, or text of a coding/algorithm problem into chat.
- Asks to set up a problem in C++ or Python.

---

## ⚠️ Critical Rules & Constraints (Zero Latency)

1. ⛔ **NEVER SEARCH THE WEB**:
   - Do **NOT** use web search or browse online for the problem statement.
   - Most interview and OA questions are proprietary, recent, or modified.
   - Web searches waste multiple agent turns, trigger permission dialogs, and cause significant latency.
   - Formulate everything directly from the user's provided image, screenshot, or text.

2. ⛔ **NO PRE-FLIGHT EXPLORATION OR SCRATCH PRE-TESTING**:
   - Do **NOT** run exploratory commands like `which harpy`, `find`, `ls`, `harpy --help`, or `harpy init`.
   - Do **NOT** write temporary scripts in `scratch/` to manually test the Python oracle first.
   - `harpy create` automatically runs and verifies the oracle across all test cases internally and displays any execution traceback if it fails.

3. ⛔ **NO REDUNDANT C++ REFERENCE SOLVERS**:
   - Do **NOT** write, compile, or run a C++ reference solver.
   - The Python reference oracle (`reference_code`) inside the specification automatically executes across all test cases and generates authoritative expected outputs with zero compilation overhead.

4. ⛔ **USER IMPLEMENTS `solve(...)` (LeetCode-style)**:
   - For C++ (`<problem_slug>.cpp`), fast I/O is handled in `main()` which passes typed arguments to `solve(...)`.
   - For Python (`<problem_slug>.py`), input reading and fast I/O are handled in `__main__` which calls `solve()`.
   - **NEVER implement the algorithmic logic inside `solve(...)`**. The user writes their own algorithm.

5. 💡 **LANGUAGE SELECTION (C++ vs Python)**:
   - Default to C++ (`cpp`).
   - If the user explicitly asks for Python, or if the system lacks a C++ compiler (`g++` / `clang++`), pass `--lang py` to `harpy create`.

---

## ⚡ Direct 1-Turn Setup: Pipe JSON to `harpy create -`

Do not create intermediate scratch files. Execute problem setup in **a single terminal command** using a heredoc:

### For C++:
```bash
harpy create --async - << 'EOF'
{
  "title": "Lexicographically Minimal Walk",
  "category": "graph-algorithms",
  "difficulty": "Medium",
  "tags": ["Graph", "BFS", "Shortest Path"],
  "description": "Given a directed graph with characters on edges, find the lexicographically smallest path...",
  "input_format": "The first line contains N and M...",
  "output_format": "Print the string formed by the walk...",
  "constraints": [
    "$1 \\le N, M \\le 10^5$",
    "Edges consist of lowercase Latin letters."
  ],
  "cpp_signature": "string solve(int n, int m, int k, const vector<vector<pair<int, char>>>& adj)",
  "cpp_main_parser": "int n, m, k;\ncin >> n >> m >> k;\nvector<vector<pair<int, char>>> adj(n + 1);\nfor (int i = 0; i < m; ++i) {\n    int u, v; char c;\n    cin >> u >> v >> c;\n    adj[u].push_back({v, c});\n}\ncout << solve(n, m, k, adj) << \"\\n\";",
  "testcases": [
    {"input": "4 4 2\n1 2 a\n2 4 b\n1 3 a\n3 4 a\n", "kind": "sample"}
  ],
  "reference_code": "import sys\n# Python reference solver reading sys.stdin and printing the correct answer\ndef solve():\n    lines = sys.stdin.read().split()\n    ...\nsolve()\n",
  "test_generator": "def generate():\n    # Minimal / Edge cases\n    yield ('1 0 1\\n', 'edge')\n    # Stress cases (programmatic synthesis without typing!)\n    import random\n    yield (f'100 200 50\\n' + '...', 'stress')\n"
}
EOF
```

### For Python:
```bash
harpy create --lang py --async - << 'EOF'
{
  "title": "Lexicographically Minimal Walk",
  "category": "graph-algorithms",
  "difficulty": "Medium",
  "tags": ["Graph", "BFS", "Shortest Path"],
  "description": "Given a directed graph with characters on edges, find the lexicographically smallest path...",
  "input_format": "The first line contains N and M...",
  "output_format": "Print the string formed by the walk...",
  "constraints": [
    "$1 \\le N, M \\le 10^5$",
    "Edges consist of lowercase Latin letters."
  ],
  "testcases": [
    {"input": "4 4 2\n1 2 a\n2 4 b\n1 3 a\n3 4 a\n", "kind": "sample"}
  ],
  "reference_code": "import sys\ndef solve():\n    ...\nsolve()\n",
  "test_generator": "def generate():\n    yield ('1 0 1\\n', 'edge')\n"
}
EOF
```

> [!TIP]
> **Sub-Second Scaffolding with `--async`**:
> Using `--async` scaffolds the workspace, writes the starter code file, and registers the sample test cases in CPH in **under 0.2 seconds** so the user can start coding immediately.
> In the background, Harpy automatically synthesizes stress/edge cases from `test_generator`, verifies them with `reference_code` using the fast single-process batch oracle, and appends them to CPH and `tests/`!

#### CSES Categories:
Classify into one of the 12 standard CSES categories:
- `dynamic-programming` (knapsack, LIS, grid DP)
- `graph-algorithms` (BFS, DFS, Dijkstra, flows)
- `tree-algorithms` (tree traversals, LCA, diameter)
- `sorting-and-searching` (binary search, two pointers)
- `greedy-algorithms` (intervals, scheduling)
- `range-queries` (segment tree, Fenwick, prefix sums)
- `mathematics` (number theory, combinatorics, modular arithmetic)
- `string-algorithms` (hashing, KMP, trie)
- `geometry` (convex hull, polygon)
- `bit-manipulation` (bitmasks, XOR)
- `introductory-problems` (simulation, basic loops)
- `advanced-techniques`

**What `harpy create` automatically accomplishes in this 1 step:**
1. Runs the Python `reference_code` across all test cases to verify and generate exact outputs.
2. Scaffolds `problems/<category>/<slug>/` containing:
   - `problem.md` (LeetCode specification with LaTeX formulas)
   - `<slug>.cpp` or `<slug>.py` (Starter code with typed signature / starter template)
   - `tests/in_*.txt` & `tests/out_*.txt`
   - `problem.json`
3. Writes `.cph/.<slug>.<ext>_<hash>.prob` for offline testing.
4. Attempts HTTP sync with active CPH extension listener on port 27121.

---

## 3. Present to the User
Report:
- Summary of the problem, category, and constraints.
- Direct clickable link to starter file: [`problems/<category>/<slug>/<slug>.<ext>`](file://problems/<category>/<slug>/<slug>.<ext>).
- Summary of verified test cases (sample, edge, stress).
- The exact test command:
  ```bash
  harpy test <slug>
  ```
  *(Harpy CLI automatically searches across all category folders and handles both C++ and Python).*

---

## 4. Testing the User's Solution
When the user says "test my code", "run tests", or asks for debugging:
1. Run `harpy test <slug>`.
2. Display the Rich test results (PASS / FAIL / TLE / RTE) and explain any failures if requested.
