from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp.server.mcpserver import MCPServer
from harpy.cph import dispatch_to_cph, write_cph_file
from harpy.formatter import create_problem_workspace
from harpy.models import ProblemSpec, TestCase, TestCaseKind
from harpy.oracle import verify_and_generate_testcases
from harpy.runner import SolutionRunner, compare_outputs


server = MCPServer("harpy")


@server.tool()
def harpy_setup_problem(
    title: str,
    description: str,
    difficulty: str = "Medium",
    tags: Optional[List[str]] = None,
    input_format: str = "",
    output_format: str = "",
    constraints: Optional[List[str]] = None,
    time_limit_ms: int = 1000,
    memory_limit_mb: int = 256,
    lang: str = "cpp",
    base_dir: str = ".",
    cpp_signature: Optional[str] = None,
    cpp_main_parser: Optional[str] = None,
) -> str:
    """
    Format a competitive programming / LeetCode problem, generate markdown,
    starter code, and directory structure.
    """
    spec = ProblemSpec(
        title=title,
        difficulty=difficulty,
        tags=tags or [],
        description=description,
        input_format=input_format,
        output_format=output_format,
        constraints=constraints or [],
        time_limit_ms=time_limit_ms,
        memory_limit_mb=memory_limit_mb,
        cpp_signature=cpp_signature,
        cpp_main_parser=cpp_main_parser,
    )

    ws = create_problem_workspace(spec, base_dir=base_dir, lang=lang)

    # Save problem.json for persistence and CPH push
    json_path = ws["dir"] / "problem.json"
    json_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    return json.dumps(
        {
            "status": "success",
            "slug": spec.get_slug(),
            "workspace_dir": str(ws["dir"].resolve()),
            "markdown_file": str(ws["markdown"].resolve()),
            "solution_file": str(ws["solution"].resolve()),
            "tests_dir": str(ws["tests_dir"].resolve()),
        },
        indent=2,
    )


@server.tool()
def harpy_oracle_generate_tests(
    problem_dir: str,
    reference_python_code: str,
    inputs: List[Dict[str, Any]],
    timeout_sec: float = 3.0,
) -> str:
    """
    Run a Python reference oracle on given input test candidates to compute
    authoritative, guaranteed expected outputs, saving them to tests/ and problem.json.
    Each item in inputs: {"input": "...", "kind": "sample"|"edge"|"stress", "explanation": "..."}
    """
    prob_path = Path(problem_dir).resolve()
    spec_json = prob_path / "problem.json"

    if not spec_json.exists():
        return json.dumps(
            {"status": "error", "message": f"problem.json not found in {problem_dir}"}
        )

    spec = ProblemSpec.model_validate_json(spec_json.read_text(encoding="utf-8"))
    spec.reference_code = reference_python_code

    input_tuples = [
        (
            item.get("input", ""),
            TestCaseKind(item.get("kind", "sample")),
            item.get("explanation"),
        )
        for item in inputs
    ]

    try:
        verified_cases = verify_and_generate_testcases(
            reference_python_code, input_tuples, timeout_sec=timeout_sec
        )
        spec.testcases = verified_cases

        # Update problem.json and problem.md
        spec_json.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
        (prob_path / "problem.md").write_text(spec.to_markdown(), encoding="utf-8")

        # Update tests/ directory
        tests_dir = prob_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        for idx, tc in enumerate(spec.testcases, 1):
            (tests_dir / f"in_{idx:02d}.txt").write_text(
                tc.normalized_input(), encoding="utf-8"
            )
            (tests_dir / f"out_{idx:02d}.txt").write_text(
                (tc.normalized_output() + "\n") if tc.output else "", encoding="utf-8"
            )

        return json.dumps(
            {
                "status": "success",
                "testcases_count": len(verified_cases),
                "summary": [
                    {
                        "id": tc.id,
                        "kind": tc.kind.value,
                        "input_preview": tc.input[:60].replace("\n", "\\n"),
                        "output_preview": tc.output[:60].replace("\n", "\\n"),
                    }
                    for tc in verified_cases
                ],
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


@server.tool()
def harpy_sync_cph(
    problem_dir: str,
    solution_file: Optional[str] = None,
    port: int = 27121,
) -> str:
    """
    Syncs test cases and problem metadata to CPH:
    1. Writes .cph/<file>.prob directly in workspace.
    2. Sends HTTP POST to CPH/Competitive Companion listener on specified port.
    """
    prob_path = Path(problem_dir).resolve()
    spec_json = prob_path / "problem.json"

    if not spec_json.exists():
        return json.dumps(
            {"status": "error", "message": f"problem.json not found in {problem_dir}"}
        )

    spec = ProblemSpec.model_validate_json(spec_json.read_text(encoding="utf-8"))

    # Determine solution file
    if solution_file:
        sol_path = Path(solution_file).resolve()
    else:
        candidates = list(prob_path.glob("solution.*"))
        sol_path = candidates[0] if candidates else (prob_path / "solution.cpp")

    # 1. Write .cph file directly
    cph_file = write_cph_file(spec, sol_path)

    # 2. Attempt HTTP dispatch to active CPH listener
    http_result = dispatch_to_cph(spec, ports=[port, 10045, 10043])

    return json.dumps(
        {
            "status": "success",
            "cph_file": str(cph_file),
            "http_dispatch": http_result,
        },
        indent=2,
    )


@server.tool()
def harpy_test_solution(
    solution_file: str,
    time_limit_ms: int = 2000,
) -> str:
    """
    Compile and test a solution file (C++, Python, Java) against test cases in tests/.
    Returns detailed pass/fail report with execution times.
    """
    sol_path = Path(solution_file).resolve()
    if not sol_path.exists():
        return json.dumps(
            {"status": "error", "message": f"Solution file not found: {solution_file}"}
        )

    prob_dir = sol_path.parent
    tests_dir = prob_dir / "tests"

    testcases = []
    if tests_dir.exists():
        in_files = sorted(tests_dir.glob("in_*.txt"))
        for in_file in in_files:
            idx_str = in_file.stem.replace("in_", "")
            out_file = tests_dir / f"out_{idx_str}.txt"
            in_content = in_file.read_text(encoding="utf-8")
            out_content = (
                out_file.read_text(encoding="utf-8") if out_file.exists() else ""
            )
            testcases.append(
                TestCase(
                    id=idx_str,
                    input=in_content,
                    output=out_content,
                    kind=TestCaseKind.SAMPLE,
                )
            )

    if not testcases:
        return json.dumps(
            {"status": "error", "message": f"No test cases found in {tests_dir}"}
        )

    runner = SolutionRunner(sol_path, time_limit_ms=time_limit_ms)
    ok, compile_err = runner.compile()
    if not ok:
        runner.cleanup()
        return json.dumps(
            {"status": "error", "error_type": "CE", "details": compile_err}
        )

    results = []
    for tc in testcases:
        res = runner.run_case(tc)
        results.append(
            {
                "case_id": tc.id,
                "status": res.status,
                "time_ms": round(res.execution_time_ms, 2),
                "actual_output": res.actual_output.strip(),
                "expected_output": res.expected_output.strip(),
                "stderr": res.stderr.strip() if res.stderr else "",
            }
        )

    runner.cleanup()
    all_passed = all(r["status"] == "PASS" for r in results)

    return json.dumps(
        {
            "status": "success",
            "all_passed": all_passed,
            "passed_count": sum(1 for r in results if r["status"] == "PASS"),
            "total_count": len(results),
            "results": results,
        },
        indent=2,
    )


def main():
    import asyncio
    asyncio.run(server.run_stdio_async())


if __name__ == "__main__":
    main()
