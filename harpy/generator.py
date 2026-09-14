from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

from harpy.cph import dispatch_to_cph, write_cph_file
from harpy.models import ProblemSpec, TestCase
from harpy.oracle import execute_test_generator, get_python_interpreter, verify_and_generate_testcases


def find_problem_path(target: Path | str, base_dir: str = ".") -> Optional[Path]:
    """Find problem directory from path, name, or slug."""
    p = Path(target)
    if (p / "problem.json").is_file():
        return p.resolve()
    if p.is_file() and p.name == "problem.json":
        return p.parent.resolve()

    # Search in problems/ directory
    base = Path(base_dir).resolve()
    prob_root = base / "problems" if (base / "problems").is_dir() else base
    for cand in prob_root.glob("**/problem.json"):
        if cand.parent.name == str(target) or cand.parent.name.lower() == str(target).lower():
            return cand.parent.resolve()
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
            if data.get("title", "").lower() == str(target).lower():
                return cand.parent.resolve()
        except Exception:
            pass

    return None


def execute_test_generation_for_problem(
    problem_target: Path | str,
    oracle_code: Optional[str] = None,
    generator_code: Optional[str] = None,
) -> Tuple[int, str]:
    """
    Executes test generation and oracle verification for a problem,
    appending new verified test cases to tests/, problem.json, and .cph.
    Returns (num_new_tests, message).
    """
    prob_dir = find_problem_path(problem_target)
    if not prob_dir:
        return 0, f"Could not locate problem directory for '{problem_target}'"

    spec_json = prob_dir / "problem.json"
    if not spec_json.is_file():
        return 0, f"problem.json not found in {prob_dir}"

    try:
        spec = ProblemSpec.model_validate_json(spec_json.read_text(encoding="utf-8"))
    except Exception as e:
        return 0, f"Failed to parse problem.json: {e}"

    ref_code = oracle_code or spec.reference_code
    gen_code = generator_code or spec.test_generator

    if not gen_code:
        return 0, "No test_generator specified in problem.json or arguments"
    if not ref_code:
        return 0, "No reference_code (oracle) specified in problem.json or arguments"

    # 1. Run algorithmic generator
    try:
        generated_tuples = execute_test_generator(gen_code)
    except Exception as e:
        return 0, f"Test generator error: {e}"

    if not generated_tuples:
        return 0, "Test generator yielded 0 test cases"

    # 2. Filter out already present inputs
    existing_inputs = set()
    for tc in spec.testcases:
        norm = tc.normalized_input().strip()
        existing_inputs.add(norm)

    new_tuples = []
    for item in generated_tuples:
        raw_norm = item[0].replace("\r\n", "\n").strip()
        if raw_norm not in existing_inputs:
            new_tuples.append(item)
            existing_inputs.add(raw_norm)

    if not new_tuples:
        return 0, "All generated test inputs already exist in problem specification"

    # 3. Verify and generate authoritative outputs with batch oracle
    try:
        verified_cases = verify_and_generate_testcases(
            ref_code,
            new_tuples,
            timeout_sec=float(spec.time_limit_ms) / 1000.0 + 2.0,
        )
    except Exception as e:
        return 0, f"Reference oracle verification failed: {e}"

    # 4. Save test cases to tests/ and append to spec
    tests_dir = prob_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    max_id = max([tc.id for tc in spec.testcases] or [0])
    appended_cases: list[TestCase] = []

    for offset, tc in enumerate(verified_cases, 1):
        new_id = max_id + offset
        tc_final = TestCase(
            id=new_id,
            input=tc.input,
            output=tc.output,
            kind=tc.kind,
            explanation=tc.explanation,
        )
        in_file = tests_dir / f"in_{new_id:02d}.txt"
        out_file = tests_dir / f"out_{new_id:02d}.txt"
        in_file.write_text(tc_final.normalized_input(), encoding="utf-8")
        out_file.write_text(tc_final.normalized_output(), encoding="utf-8")

        spec.testcases.append(tc_final)
        appended_cases.append(tc_final)

    # 5. Update problem.json
    spec_json.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    # 6. Update CPH files
    sol_file = prob_dir / f"{spec.get_slug()}.cpp"
    if not sol_file.exists():
        sol_file = prob_dir / "solution.cpp"
    if not sol_file.exists():
        cpps = list(prob_dir.glob("*.cpp"))
        if cpps:
            sol_file = cpps[0]
        else:
            sol_file = prob_dir / f"{spec.get_slug()}.cpp"

    write_cph_file(spec, sol_file)
    dispatch_to_cph(spec)

    return len(appended_cases), f"Successfully generated and verified {len(appended_cases)} test cases in {prob_dir}"


def spawn_background_test_generation(problem_dir: Path | str) -> int:
    """
    Spawns a detached background process to generate and verify test cases.
    Returns the process PID.
    """
    p_dir = Path(problem_dir).resolve()
    log_file = p_dir / ".generator.log"
    log_fp = open(log_file, "a", encoding="utf-8")
    log_fp.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Spawning background test generator for {p_dir.name}...\n")
    log_fp.flush()

    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "generate-tests", str(p_dir)]
    else:
        cmd = [get_python_interpreter(), "-m", "harpy.cli", "generate-tests", str(p_dir)]

    # When spawned from a PyInstaller onefile binary, child processes must not inherit
    # _PYI_APPLICATION_HOME_DIR, _MEIPASS, or parent's LD_LIBRARY_PATH. Otherwise, the child
    # attempts to use the parent's temporary extraction folder which gets deleted when parent exits.
    child_env = os.environ.copy()
    for key in list(child_env.keys()):
        if key.startswith("_PYI_") or "MEI" in key:
            child_env.pop(key, None)
    if "LD_LIBRARY_PATH_ORIG" in child_env:
        child_env["LD_LIBRARY_PATH"] = child_env["LD_LIBRARY_PATH_ORIG"]
    else:
        child_env.pop("LD_LIBRARY_PATH", None)

    proc = subprocess.Popen(
        cmd,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=child_env,
    )
    return proc.pid
