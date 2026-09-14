from __future__ import annotations

import json
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


class GeneratorExecutionError(Exception):
    pass


class GeneratorTimeoutError(Exception):
    pass


GENERATOR_WRAPPER_TEMPLATE = """
import sys
import json

# Injected user generator code
__USER_CODE_PLACEHOLDER__

def __harpy_collect_cases():
    items = []
    gen_func = None
    for fname in ('generate', 'generate_inputs', 'generate_testcases', 'test_cases'):
        if fname in globals() and callable(globals()[fname]):
            gen_func = globals()[fname]
            break

    if gen_func:
        res = gen_func()
        if hasattr(res, '__iter__') and not isinstance(res, (str, bytes, dict)):
            for x in res:
                items.append(x)
        else:
            items.append(res)
    elif 'test_cases' in globals() and isinstance(globals()['test_cases'], list):
        items.extend(globals()['test_cases'])
    elif 'cases' in globals() and isinstance(globals()['cases'], list):
        items.extend(globals()['cases'])

    formatted = []
    for item in items:
        if isinstance(item, (tuple, list)):
            raw_in = str(item[0])
            kind = str(item[1]) if len(item) > 1 else "sample"
            expl = str(item[2]) if len(item) > 2 and item[2] is not None else None
            formatted.append({"input": raw_in, "kind": kind, "explanation": expl})
        elif isinstance(item, dict):
            formatted.append({
                "input": str(item.get("input", "")),
                "kind": str(item.get("kind", "sample")),
                "explanation": item.get("explanation"),
            })
        elif isinstance(item, str):
            formatted.append({"input": item, "kind": "sample", "explanation": None})

    print("###HARPY_GENERATOR_JSON_START###")
    print(json.dumps(formatted))
    print("###HARPY_GENERATOR_JSON_END###")

if __name__ == '__main__':
    __harpy_collect_cases()
"""


def execute_test_generator(
    generator_code: str,
    timeout_sec: float = 10.0,
) -> List[Tuple[str, TestCaseKind, Optional[str]]]:
    """
    Executes a Python test generator script in a subprocess and extracts
    the generated input candidates.
    """
    wrapper = GENERATOR_WRAPPER_TEMPLATE.replace(
        "__USER_CODE_PLACEHOLDER__", generator_code
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(wrapper)
        temp_path = f.name

    try:
        proc = subprocess.run(
            [get_python_interpreter(), temp_path],
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if proc.returncode != 0:
            raise GeneratorExecutionError(
                f"Test generator exited with code {proc.returncode}.\nStderr: {proc.stderr}"
            )
        stdout = proc.stdout
        if "###HARPY_GENERATOR_JSON_START###" not in stdout:
            raise GeneratorExecutionError(
                f"Test generator produced no output marker.\nStdout: {stdout}\nStderr: {proc.stderr}"
            )
        json_str = stdout.split("###HARPY_GENERATOR_JSON_START###")[1].split(
            "###HARPY_GENERATOR_JSON_END###"
        )[0].strip()
        data = json.loads(json_str)

        results: List[Tuple[str, TestCaseKind, Optional[str]]] = []
        for item in data:
            raw_in = item.get("input", "")
            kind_str = item.get("kind", "sample").lower()
            try:
                kind = TestCaseKind(kind_str)
            except ValueError:
                kind = TestCaseKind.SAMPLE
            expl = item.get("explanation")
            results.append((raw_in, kind, expl))
        return results
    except subprocess.TimeoutExpired:
        raise GeneratorTimeoutError(
            f"Test generator timed out after {timeout_sec}s."
        )
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
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
