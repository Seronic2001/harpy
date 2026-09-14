from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from harpy.models import TestCase, TestCaseKind


def get_python_interpreter() -> str:
    """Get path to a Python interpreter, safe for both virtualenv and PyInstaller frozen binaries."""
    if getattr(sys, "frozen", False):
        return shutil.which("python3") or shutil.which("python") or "python3"
    return sys.executable


class OracleExecutionError(Exception):
    pass


class OracleTimeoutError(Exception):
    pass


def run_reference_solution(
    python_code: str,
    raw_input: str,
    timeout_sec: float = 3.0,
) -> str:
    """
    Safely executes the Python reference solution against raw_input and returns stdout.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(python_code)
        temp_path = f.name

    try:
        proc = subprocess.run(
            [get_python_interpreter(), temp_path],
            input=raw_input,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if proc.returncode != 0:
            raise OracleExecutionError(
                f"Oracle exited with code {proc.returncode}.\nStderr: {proc.stderr}\nInput:\n{raw_input}"
            )
        return proc.stdout
    except subprocess.TimeoutExpired:
        raise OracleTimeoutError(
            f"Oracle timed out after {timeout_sec}s on input:\n{raw_input[:200]}"
        )
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass


def verify_and_generate_testcases(
    reference_python_code: str,
    inputs: List[Tuple[str, TestCaseKind, Optional[str]]],
    timeout_sec: float = 3.0,
) -> List[TestCase]:
    """
    Runs the reference python code across all input candidates and builds
    guaranteed, verified TestCase objects.
    Each item in inputs is (raw_input_str, kind, optional_explanation).
    """
    verified_cases: List[TestCase] = []
    for idx, (raw_in, kind, explanation) in enumerate(inputs, 1):
        clean_in = raw_in.replace("\r\n", "\n")
        if clean_in and not clean_in.endswith("\n"):
            clean_in += "\n"

        expected_out = run_reference_solution(
            reference_python_code, clean_in, timeout_sec=timeout_sec
        )
        verified_cases.append(
            TestCase(
                id=idx,
                input=clean_in,
                output=expected_out,
                kind=kind,
                explanation=explanation,
            )
        )
    return verified_cases
