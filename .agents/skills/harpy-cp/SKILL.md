---
name: harpy-cp
description: Formulates algorithm problems from uploaded images or raw text into LeetCode-style markdown specifications, generates verified test cases using a Python reference oracle, creates a starter <problem_slug>.cpp file with an empty void solve() for the user to implement, syncs with CPH, and tests solutions.
---

# Harpy Competitive Programming Workflow

Follow this procedure whenever the user:
- Uploads an image, screenshot, whiteboard photo, or text of a coding/algorithm problem into chat.
- Asks to set up a problem in C++ (or Python).

---

## The Workflow Protocol

### 1. Extract & Standardize Problem
From the provided image or text:
1. Determine:
   - **Title**: Clean descriptive title (e.g., "Maximum Subarray Sum").
   - **Slug**: Kebab-case name (e.g., `maximum-subarray-sum`).
   - **Difficulty**: "Easy", "Medium", or "Hard".
   - **Topics**: e.g., `["Dynamic Programming", "Two Pointers"]`.
   - **Description**: Clear problem statement.
   - **Input & Output Format**: Precise specifications.
   - **Constraints**: Express with LaTeX math (e.g., `$1 \le N \le 10^5$`).
2. Run `harpy_setup_problem` or Harpy API to create:
   - `problems/<slug>/problem.md`
   - `problems/<slug>/<slug>.cpp`

### 2. File Template Requirement: User Implements `solve(...)` (LeetCode-style)
The starter code file **must be named `<problem_slug>.cpp`** and must:
1. Include the problem description, constraints, and sample examples in comments at the top.
2. Read all input in `main()` (with fast I/O) and pass the parsed inputs into `solve(...)` with clean, typed parameters (e.g. `int n, int m, const vector<string>& grid`).
3. Provide the `solve(...)` function with its signature and parameters pre-filled, but its body **left empty for the user to implement**:
   ```cpp
   // LeetCode-style signature: inputs are already parsed in main()
   auto solve(int n, int m, int k, const vector<string>& grid) {
       // Write your solution here
   }

   int main() {
       ios_base::sync_with_stdio(false);
       cin.tie(NULL);

       // Read input...
       auto result = solve(...);
       // Print result...
       return 0;
   }
   ```
> **CRITICAL RULE**: Do **NOT** implement the core algorithmic logic inside `solve(...)`. The user writes their own algorithm!

### 3. Generate Verified Test Cases (Python Reference Oracle)
1. Write a correct reference solution in Python (simulation, brute force, or mathematical).
2. Generate comprehensive test input cases:
   - Sample cases from the problem statement.
   - Corner/edge cases ($N=0, 1$, bounds, negative numbers, identical values).
   - Stress/random cases.
3. Run `harpy_oracle_generate_tests` to execute the reference Python code and produce verified test cases in `tests/` and `problem.json`.

### 4. Sync with CPH
1. Run `harpy_sync_cph` to:
   - Dispatch over HTTP to CPH (port 27121) so it opens in the editor if active.
   - Write `.cph/.<slug>.cpp_<hash>.prob` for offline support.

### 5. Present to the User
Report:
- Clean summary of the problem and constraints.
- Direct clickable link to the generated starter file: [`problems/<slug>/<slug>.cpp`](file://problems/<slug>/<slug>.cpp).
- Summary of the generated test cases (samples, edge cases).
- The exact command the user can run when ready:
   ```bash
   harpy test <slug>
   ```
   (or `harpy test problems/<slug>/<slug>.cpp`)

### 6. Testing the User's Solution
When the user says "test my code", "run tests", or asks for help debugging:
1. Run `harpy_test_solution` or execute `harpy test problems/<slug>/<slug>.cpp`.
2. Display the status (PASS / FAIL / TLE / RTE) and explain any failures if requested.
