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



BATCH_ORACLE_WRAPPER_TEMPLATE = """
import sys
import io
import json
import traceback

raw_inputs = json.loads(sys.stdin.read())
code_str = __USER_CODE_REPR__

try:
    compiled = compile(code_str, "<reference_oracle>", "exec")
except Exception as e:
    print("###HARPY_BATCH_COMPILE_ERROR###")
    print(traceback.format_exc())
    sys.exit(1)

outputs = []
for inp in raw_inputs:
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    sys.stdin = io.StringIO(inp)
    sys.stdout = io.StringIO()
    try:
        ns = {"__name__": "__main__"}
        exec(compiled, ns)
        out = sys.stdout.getvalue()
        outputs.append({"success": True, "output": out})
    except SystemExit:
        out = sys.stdout.getvalue()
        outputs.append({"success": True, "output": out})
    except Exception as e:
        outputs.append({"success": False, "error": traceback.format_exc()})
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout

print("###HARPY_BATCH_OUTPUT_START###")
print(json.dumps(outputs))
print("###HARPY_BATCH_OUTPUT_END###")
"""


def run_reference_solution_batch(
    python_code: str,
    raw_inputs: List[str],
    timeout_sec: float = 10.0,
) -> List[Tuple[bool, str]]:
    """
    Executes the Python reference solution across multiple inputs in a single
    process, returning a list of (success, output_or_error) for each input.
    """
    if not raw_inputs:
        return []

    wrapper = BATCH_ORACLE_WRAPPER_TEMPLATE.replace(
        "__USER_CODE_REPR__", repr(python_code)
    )
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(wrapper)
        temp_path = f.name

    try:
        proc = subprocess.run(
            [get_python_interpreter(), temp_path],
            input=json.dumps(raw_inputs),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        if proc.returncode != 0:
            if "###HARPY_BATCH_COMPILE_ERROR###" in proc.stdout:
                err = proc.stdout.split("###HARPY_BATCH_COMPILE_ERROR###")[1].strip()
                raise OracleExecutionError(f"Oracle compilation failed:\n{err}")
            raise OracleExecutionError(
                f"Oracle batch runner exited with code {proc.returncode}.\nStderr: {proc.stderr}\nStdout: {proc.stdout}"
            )
        stdout = proc.stdout
        if "###HARPY_BATCH_OUTPUT_START###" not in stdout:
            raise OracleExecutionError(
                f"Oracle batch produced no output marker.\nStdout: {stdout}\nStderr: {proc.stderr}"
            )
        json_str = stdout.split("###HARPY_BATCH_OUTPUT_START###")[1].split(
            "###HARPY_BATCH_OUTPUT_END###"
        )[0].strip()
        data = json.loads(json_str)
        results: List[Tuple[bool, str]] = []
        for item in data:
            if item.get("success"):
                results.append((True, item.get("output", "")))
            else:
                results.append((False, item.get("error", "")))
        return results
    except subprocess.TimeoutExpired:
        raise OracleTimeoutError(
            f"Oracle batch execution timed out after {timeout_sec}s."
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
    Uses fast single-process batch execution, falling back to per-test execution if needed.
    """
    if not inputs:
        return []

    clean_inputs: List[str] = []
    for raw_in, kind, explanation in inputs:
        clean_in = raw_in.replace("\r\n", "\n")
        if clean_in and not clean_in.endswith("\n"):
            clean_in += "\n"
        clean_inputs.append(clean_in)

    batch_timeout = max(timeout_sec * len(inputs), 10.0)
    try:
        batch_results = run_reference_solution_batch(
            reference_python_code, clean_inputs, timeout_sec=batch_timeout
        )
        verified_cases: List[TestCase] = []
        for idx, ((raw_in, kind, explanation), (success, out_or_err)) in enumerate(
            zip(inputs, batch_results), 1
        ):
            if not success:
                raise OracleExecutionError(
                    f"Oracle failed on test case {idx}:\n{out_or_err}\nInput:\n{clean_inputs[idx-1]}"
                )
            verified_cases.append(
                TestCase(
                    id=idx,
                    input=clean_inputs[idx - 1],
                    output=out_or_err,
                    kind=kind,
                    explanation=explanation,
                )
            )
        return verified_cases
    except (OracleExecutionError, OracleTimeoutError):
        raise
    except Exception:
        # Fallback to serial runner if unexpected batch harness failure
        verified_cases = []
        for idx, (clean_in, (raw_in, kind, explanation)) in enumerate(
            zip(clean_inputs, inputs), 1
        ):
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
