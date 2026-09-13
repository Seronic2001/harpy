---
name: harpy-cp
description: Formulates algorithm problems from uploaded images or raw text into LeetCode-style markdown specifications, generates verified test cases using a Python reference oracle, syncs with CPH (Competitive Programming Helper), and tests solutions.
---

# Harpy Competitive Programming Workflow

Use this skill whenever the user:
- Uploads an image, screenshot, whiteboard photo, or text snippet of an algorithm / coding problem.
- Asks to format a problem in LeetCode/Codeforces style.
- Asks to generate test cases or corner cases for a problem.
- Wants to set up a CPH (Competitive Programming Helper) workspace or test a solution.

---

## The Step-by-Step Procedure

### Step 1: Multimodal Problem Extraction & Standardization
When an image or problem text is provided:
1. Extract and standardize the problem details:
   - **Title**: Clean descriptive name (e.g., "Subarray Sum Equals K").
   - **Difficulty**: "Easy", "Medium", or "Hard".
   - **Tags**: Algorithms/data structures involved (e.g., `["Prefix Sum", "Hash Table"]`).
   - **Description**: Precise explanation of the problem statement.
   - **Input Format**: Describe stdin lines, array dimensions, tokens.
   - **Output Format**: Expected stdout.
   - **Constraints**: Express with LaTeX math (e.g., `$1 \le N \le 10^5$`, `$-10^9 \le A_i \le 10^9$`, Time: 1000 ms, Memory: 256 MB).
2. Call `harpy_setup_problem` or run the Python API:
   ```python
   from harpy.formatter import create_problem_workspace
   from harpy.models import ProblemSpec
   # Sets up <slug>/problem.md, <slug>/solution.cpp, <slug>/tests/
   ```

### Step 2: Test Generation with Python Reference Oracle
**Never guess or hallucinate outputs for non-trivial inputs.**
1. Write a correct reference solution in Python (simulation, greedy, or brute force).
2. Prepare a diverse set of test inputs:
   - **Sample Cases**: Taken directly from the problem statement.
   - **Edge/Corner Cases**:
     - Minimal constraint ($N = 0$ or $N = 1$).
     - Maximal constraint values (overflow checks, large numbers).
     - Empty inputs, all negative, all identical elements.
     - Sorted, reverse-sorted, or alternating values.
   - **Stress/Random Cases**: Generated within constraints.
3. Call `harpy_oracle_generate_tests` to execute the reference Python code on the inputs and save the verified outputs.

### Step 3: CPH Sync & Workspace Setup
1. Call `harpy_sync_cph(problem_dir)`:
   - Sends an HTTP POST to CPH on port `27121` (Competitive Companion protocol). If CPH is active in VS Code, the problem pops up immediately.
   - Also writes `.cph/.<solution>_<hash>.prob` directly in the problem folder, guaranteeing tests are available offline as soon as the file is opened in VS Code.
2. Link the user to `problem.md` and `solution.cpp` (or `solution.py`).

### Step 4: Testing Solutions
When the user implements or requests to test their solution:
1. Call `harpy_test_solution(solution_path)` or run CLI:
   ```bash
   ./.venv/bin/harpy test <slug>/solution.cpp
   ```
2. Report the color-coded results: execution time, memory, pass/fail status, and any diff details.
