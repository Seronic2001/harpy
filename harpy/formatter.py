from __future__ import annotations

import os
from pathlib import Path
from typing import Dict
from harpy.models import ProblemSpec, TestCaseKind


def generate_cpp_starter(spec: ProblemSpec) -> str:
    """Generate competitive programming C++ starter template with LeetCode-style solve()."""
    desc_lines = spec.description.strip().splitlines()
    desc_comment = "\n * ".join(desc_lines)

    constraints_comment = "\n * ".join(f"- {c}" for c in spec.constraints) if spec.constraints else "None specified"

    examples_block = []
    sample_idx = 1
    for tc in spec.testcases:
        if tc.kind == TestCaseKind.SAMPLE:
            ex_lines = [
                f"Example {sample_idx}:",
                f"   Input:  {tc.input.strip().replace(chr(10), ' ')}",
                f"   Output: {tc.output.strip().replace(chr(10), ' ')}",
            ]
            if tc.explanation:
                ex_lines.append(f"   Explanation: {tc.explanation}")
            examples_block.append("\n * ".join(ex_lines))
            sample_idx += 1

    examples_comment = "\n *\n * ".join(examples_block) if examples_block else "See problem description."

    return f"""/**
 * Problem: {spec.title}
 * Difficulty: {spec.difficulty}
 * Time Limit: {spec.time_limit_ms} ms | Memory Limit: {spec.memory_limit_mb} MB
 *
 * Description:
 * {desc_comment}
 *
 * Constraints:
 * {constraints_comment}
 *
 * Examples:
 * {examples_comment}
 */

#include <bits/stdc++.h>
using namespace std;

void solve() {{
    // Write your solution here
}}

int main() {{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t = 1;
    // cin >> t; // Uncomment if multiple test cases exist per run

    while (t--) {{
        solve();
    }}

    return 0;
}}
"""


def generate_python_starter(spec: ProblemSpec) -> str:
    """Generate competitive programming Python starter template."""
    return f'''"""
Problem: {spec.title}
Difficulty: {spec.difficulty}
Time Limit: {spec.time_limit_ms} ms | Memory Limit: {spec.memory_limit_mb} MB
"""

import sys

def solve():
    # Write your solution here
    pass

if __name__ == "__main__":
    solve()
'''


DEFAULT_GENERATORS = {
    "cpp": generate_cpp_starter,
    "py": generate_python_starter,
    "python": generate_python_starter,
}


def create_problem_workspace(
    spec: ProblemSpec,
    base_dir: Path | str = ".",
    lang: str = "cpp",
) -> Dict[str, Path]:
    """
    Creates a standardized folder for the problem:
    <base_dir>/<slug>/
       problem.md
       <slug>.<lang> (main starter file for the user)
       solution.<lang> (symlinked/mirrored)
       tests/
          in_1.txt, out_1.txt, ...
    """
    slug = spec.get_slug()
    base = Path(base_dir).resolve() / slug
    base.mkdir(parents=True, exist_ok=True)

    # 1. Write problem.md
    md_path = base / "problem.md"
    md_path.write_text(spec.to_markdown(), encoding="utf-8")

    # 2. Write starter code named <slug>.<ext>
    ext = "cpp" if lang == "cpp" else ("py" if lang in ("py", "python") else "java")
    main_code_path = base / f"{slug}.{ext}"
    compat_code_path = base / f"solution.{ext}"

    generator = DEFAULT_GENERATORS.get(lang, generate_cpp_starter)
    starter_code = generator(spec)

    if not main_code_path.exists():
        main_code_path.write_text(starter_code, encoding="utf-8")

    if not compat_code_path.exists():
        compat_code_path.write_text(starter_code, encoding="utf-8")

    # 3. Write test cases
    tests_dir = base / "tests"
    tests_dir.mkdir(exist_ok=True)
    for idx, tc in enumerate(spec.testcases, 1):
        in_file = tests_dir / f"in_{idx:02d}.txt"
        out_file = tests_dir / f"out_{idx:02d}.txt"
        in_file.write_text(tc.normalized_input(), encoding="utf-8")
        out_file.write_text(
            (tc.normalized_output() + "\n") if tc.output else "", encoding="utf-8"
        )

    return {
        "dir": base,
        "markdown": md_path,
        "solution": main_code_path,
        "compat_solution": compat_code_path,
        "tests_dir": tests_dir,
    }
