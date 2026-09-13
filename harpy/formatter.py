from __future__ import annotations

import os
from pathlib import Path
from typing import Dict
from harpy.models import ProblemSpec


def generate_cpp_starter(spec: ProblemSpec) -> str:
    """Generate competitive programming C++ starter template."""
    return f"""/**
 * Problem: {spec.title}
 * Difficulty: {spec.difficulty}
 * Time Limit: {spec.time_limit_ms} ms | Memory Limit: {spec.memory_limit_mb} MB
 */

#include <bits/stdc++.h>
using namespace std;

void solve() {{
    // TODO: Implement solution here
}}

int main() {{
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int t = 1;
    // Uncomment if problem has multiple test cases:
    // if (!(cin >> t)) return 0;

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
    input_data = sys.stdin.read().split()
    if not input_data:
        return
    # TODO: Implement solution here
    pass

if __name__ == "__main__":
    solve()
'''


def generate_java_starter(spec: ProblemSpec) -> str:
    """Generate competitive programming Java starter template."""
    return f"""/**
 * Problem: {spec.title}
 * Difficulty: {spec.difficulty}
 */

import java.io.*;
import java.util.*;

public class Main {{
    public static void main(String[] args) throws IOException {{
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String line = br.readLine();
        if (line == null) return;
        // TODO: Implement solution here
    }}
}}
"""


DEFAULT_GENERATORS = {
    "cpp": generate_cpp_starter,
    "py": generate_python_starter,
    "python": generate_python_starter,
    "java": generate_java_starter,
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
       solution.<lang>
       tests/
          in_1.txt, out_1.txt, ...
    """
    base = Path(base_dir) / spec.get_slug()
    base.mkdir(parents=True, exist_ok=True)

    # 1. Write problem.md
    md_path = base / "problem.md"
    md_path.write_text(spec.to_markdown(), encoding="utf-8")

    # 2. Write starter code
    ext = "cpp" if lang == "cpp" else ("py" if lang in ("py", "python") else "java")
    code_path = base / f"solution.{ext}"
    if not code_path.exists():
        generator = DEFAULT_GENERATORS.get(lang, generate_cpp_starter)
        code_path.write_text(generator(spec), encoding="utf-8")

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
        "solution": code_path,
        "tests_dir": tests_dir,
    }
