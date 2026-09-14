from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from harpy.models import TestCase, TestCaseKind


console = Console()


class RunResult:
    def __init__(
        self,
        test_id: int | str,
        status: str,  # "PASS", "FAIL", "TLE", "RTE", "CE"
        execution_time_ms: float,
        actual_output: str,
        expected_output: str,
        stderr: str = "",
        kind: TestCaseKind = TestCaseKind.SAMPLE,
    ):
        self.test_id = test_id
        self.status = status
        self.execution_time_ms = execution_time_ms
        self.actual_output = actual_output
        self.expected_output = expected_output
        self.stderr = stderr
        self.kind = kind


def compare_outputs(actual: str, expected: str, float_epsilon: float = 1e-6) -> bool:
    """Compare outputs ignoring trailing whitespaces and line endings."""
    act_lines = [line.rstrip() for line in actual.strip().splitlines()]
    exp_lines = [line.rstrip() for line in expected.strip().splitlines()]

    if act_lines == exp_lines:
        return True

    # Token-level float comparison fallback
    act_tokens = actual.split()
    exp_tokens = expected.split()
    if len(act_tokens) != len(exp_tokens):
        return False

    for a, e in zip(act_tokens, exp_tokens):
        if a == e:
            continue
        try:
            fa = float(a)
            fe = float(e)
            if abs(fa - fe) > float_epsilon and abs(fa - fe) / max(1.0, abs(fe)) > float_epsilon:
                return False
        except ValueError:
            return False

    return True


class SolutionRunner:
    def __init__(self, source_path: Path | str, time_limit_ms: int = 2000):
        self.source_path = Path(source_path).resolve()
        self.time_limit_sec = max(0.5, time_limit_ms / 1000.0)
        self.temp_dir = tempfile.mkdtemp(prefix="harpy_runner_")
        self.compiled_target: Optional[Path] = None
        self.lang = self._detect_language()

    def _detect_language(self) -> str:
        ext = self.source_path.suffix.lower()
        if ext in (".cpp", ".cc", ".cxx"):
            return "cpp"
        elif ext in (".py",):
            return "python"
        elif ext in (".java",):
            return "java"
        elif ext in (".rs",):
            return "rust"
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

    def compile(self) -> Tuple[bool, str]:
        """Compile solution if needed."""
        if self.lang == "python":
            return True, ""

        if self.lang == "cpp":
            out_bin = Path(self.temp_dir) / "solution_bin"
            cmd = [
                "g++",
                "-O3",
                "-std=c++17",
                str(self.source_path),
                "-o",
                str(out_bin),
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                return False, res.stderr
            self.compiled_target = out_bin
            return True, ""

        if self.lang == "java":
            # Copy source into temp dir to compile
            dest = Path(self.temp_dir) / self.source_path.name
            shutil.copy2(self.source_path, dest)
            res = subprocess.run(["javac", str(dest)], capture_output=True, text=True)
            if res.returncode != 0:
                return False, res.stderr
            self.compiled_target = Path(self.temp_dir)
            return True, ""

        return True, ""

    def run_case(self, test: TestCase) -> RunResult:
        """Run single test case."""
        if self.lang == "cpp":
            cmd = [str(self.compiled_target)]
        elif self.lang == "python":
            py_exe = (
                shutil.which("python3")
                or shutil.which("python")
                if getattr(sys, "frozen", False)
                else sys.executable
            )
            cmd = [py_exe, str(self.source_path)]
        elif self.lang == "java":
            cmd = ["java", "-cp", str(self.compiled_target), self.source_path.stem]
        else:
            cmd = []

        start_time = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=test.normalized_input(),
                capture_output=True,
                text=True,
                timeout=self.time_limit_sec,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            if proc.returncode != 0:
                return RunResult(
                    test_id=test.id,
                    status="RTE",
                    execution_time_ms=elapsed_ms,
                    actual_output=proc.stdout,
                    expected_output=test.output,
                    stderr=proc.stderr,
                    kind=test.kind,
                )

            passed = compare_outputs(proc.stdout, test.output)
            status = "PASS" if passed else "FAIL"
            return RunResult(
                test_id=test.id,
                status=status,
                execution_time_ms=elapsed_ms,
                actual_output=proc.stdout,
                expected_output=test.output,
                stderr=proc.stderr,
                kind=test.kind,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = self.time_limit_sec * 1000.0
            return RunResult(
                test_id=test.id,
                status="TLE",
                execution_time_ms=elapsed_ms,
                actual_output="",
                expected_output=test.output,
                stderr="Time limit exceeded",
                kind=test.kind,
            )
        except Exception as e:
            return RunResult(
                test_id=test.id,
                status="RTE",
                execution_time_ms=0.0,
                actual_output="",
                expected_output=test.output,
                stderr=str(e),
                kind=test.kind,
            )

    def cleanup(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass


def execute_and_render_tests(
    source_file: Path | str,
    testcases: List[TestCase],
    time_limit_ms: int = 1500,
) -> List[RunResult]:
    """Compile, execute tests, and render formatted Rich output."""
    runner = SolutionRunner(source_file, time_limit_ms=time_limit_ms)

    console.print(
        f"\n[bold cyan]⚡ Harpy Test Runner[/bold cyan]: Testing [yellow]{Path(source_file).name}[/yellow] ({runner.lang})"
    )

    ok, compile_err = runner.compile()
    if not ok:
        console.print(Panel(compile_err, title="[bold red]Compilation Error (CE)", border_style="red"))
        runner.cleanup()
        return [
            RunResult(
                test_id=0,
                status="CE",
                execution_time_ms=0,
                actual_output="",
                expected_output="",
                stderr=compile_err,
            )
        ]

    table = Table(title="Test Results", show_header=True, header_style="bold magenta")
    table.add_column("Case #", justify="center", style="dim")
    table.add_column("Type", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Time", justify="right")

    results: List[RunResult] = []
    failures: List[RunResult] = []

    for tc in testcases:
        res = runner.run_case(tc)
        results.append(res)

        if res.status == "PASS":
            status_text = "[bold green]✔ PASS[/bold green]"
        elif res.status == "FAIL":
            status_text = "[bold red]✘ FAIL[/bold red]"
            failures.append(res)
        elif res.status == "TLE":
            status_text = "[bold yellow]⏱ TLE[/bold yellow]"
            failures.append(res)
        else:
            status_text = f"[bold magenta]⚠ {res.status}[/bold magenta]"
            failures.append(res)

        table.add_row(
            str(tc.id),
            tc.kind.value,
            status_text,
            f"{res.execution_time_ms:.1f} ms",
        )

    console.print(table)

    # Detailed report for failures
    for f in failures:
        details = Text()
        if f.status == "FAIL":
            details.append("Expected Output:\n", style="bold green")
            details.append(f.expected_output.strip() + "\n\n")
            details.append("Actual Output:\n", style="bold red")
            details.append(f.actual_output.strip() + "\n")
        elif f.status == "RTE" or f.status == "TLE":
            details.append(f"Error Details:\n{f.stderr}\n", style="bold red")

        console.print(
            Panel(
                details,
                title=f"[bold red]Failed Case #{f.test_id} ({f.status})[/bold red]",
                border_style="red",
            )
        )

    pass_count = sum(1 for r in results if r.status == "PASS")
    total_count = len(results)
    if pass_count == total_count and total_count > 0:
        console.print(f"[bold green]✨ All {total_count} test cases passed![/bold green]\n")
    else:
        console.print(
            f"[bold yellow]Summary: {pass_count}/{total_count} tests passed.[/bold yellow]\n"
        )

    runner.cleanup()
    return results
