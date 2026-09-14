---
name: harpy-cp
description: Formulates algorithm problems from uploaded images or raw text into LeetCode-style markdown specifications, generates verified test cases using a Python reference oracle, creates a starter <problem_slug>.cpp file with an empty solve(...) function with prefilled parameters for the user to implement, syncs with CPH, and tests solutions.
---

# Harpy Competitive Programming Workflow

Follow this procedure whenever the user:
- Uploads an image, screenshot, whiteboard photo, or text of a coding/algorithm problem into chat.
- Asks to set up a problem in C++ (or Python).

---

## ⚠️ Critical Rules & Constraints

1. ⛔ **NEVER SEARCH THE WEB**:
   - Do **NOT** use web search or browse online for the problem statement.
   - Most interview and OA questions are proprietary, recent, or modified.
   - Web searches waste multiple agent turns, trigger permission dialogs, and cause significant latency.
   - Formulate everything directly from the user's provided image, screenshot, or text.

2. ⛔ **NO REDUNDANT C++ REFERENCE SOLVERS**:
   - Do **NOT** write, compile, or run a C++ reference solver in `scratch/`.
   - The Python reference oracle (`reference_code`) inside the specification automatically executes across all test cases and generates authoritative expected outputs with zero compilation overhead.

3. ⛔ **USER IMPLEMENTS `solve(...)` (LeetCode-style)**:
   - In `<problem_slug>.cpp`, input reading happens in `main()` with fast I/O and passes typed arguments to `solve(...)`.
   - **NEVER implement the algorithmic logic inside `solve(...)`**. The user writes their own algorithm.

---

## ⚡ Fast-Path Protocol: 1-Command Problem Setup

The fastest and most reliable way to set up a problem (avoiding MCP discovery latency or tool gaps) is using `harpy create`.

### Step 1. Formulate `scratch/spec.json`
Write a complete JSON specification to `scratch/spec.json`:

```json
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
  "reference_code": "import sys\n# Python reference solver reading sys.stdin and printing the correct answer\ndef solve():\n    lines = sys.stdin.read().split()\n    ...\nsolve()\n",
  "testcases": [
    {"input": "4 4 2\n1 2 a\n2 4 b\n1 3 a\n3 4 a\n", "kind": "sample"},
    {"input": "1 0 1\n", "kind": "edge"},
    {"input": "...", "kind": "stress"}
  ]
}
```

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

### Step 2. Execute `harpy create`
Run the 1-step creation command in the terminal:
```bash
harpy create -s scratch/spec.json
```
*(Fallback if `harpy` binary is not in PATH: `python3 -m harpy.cli create -s scratch/spec.json`)*

**What `harpy create` automatically accomplishes in 1 step:**
1. Runs the Python `reference_code` across all test cases to verify and generate exact outputs.
2. Scaffolds `problems/<category>/<slug>/` containing:
   - `problem.md` (LeetCode specification with LaTeX formulas)
   - `<slug>.cpp` (Starter code with typed `solve(...)`)
   - `tests/in_*.txt` & `tests/out_*.txt`
   - `problem.json`
3. Writes `.cph/.<slug>.cpp_<hash>.prob` for offline testing.
4. Attempts HTTP sync with active CPH extension listener on port 27121.

*(Note: If MCP tool `harpy_setup_problem` is directly available in your session, you may call MCP tools directly as an alternative).*

---

## 3. Present to the User
Report:
- Summary of the problem, category, and constraints.
- Direct clickable link to starter file: [`problems/<category>/<slug>/<slug>.cpp`](file://problems/<category>/<slug>/<slug>.cpp).
- Summary of verified test cases (sample, edge, stress).
- The exact test command:
  ```bash
  harpy test <slug>
  ```
  *(Harpy CLI automatically searches across all category folders).*

---

## 4. Testing the User's Solution
When the user says "test my code", "run tests", or asks for debugging:
1. Run `harpy test <slug>`.
2. Display the Rich test results (PASS / FAIL / TLE / RTE) and explain any failures if requested.
