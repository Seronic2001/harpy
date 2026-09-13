from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from harpy import __version__
from harpy.cph import dispatch_to_cph, write_cph_file
from harpy.formatter import create_problem_workspace
from harpy.models import ProblemSpec, TestCase, TestCaseKind
from harpy.oracle import verify_and_generate_testcases
from harpy.runner import execute_and_render_tests


console = Console()


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests against a solution file."""
    source_path = Path(args.solution).resolve()
    if not source_path.exists():
        console.print(f"[bold red]Error: File not found:[/bold red] {source_path}")
        return 1

    prob_dir = source_path.parent
    tests_dir = prob_dir / "tests"

    testcases = []
    # 1. Look for tests in tests/
    if tests_dir.exists():
        in_files = sorted(tests_dir.glob("in_*.txt"))
        for in_file in in_files:
            idx_str = in_file.stem.replace("in_", "")
            out_file = tests_dir / f"out_{idx_str}.txt"
            in_content = in_file.read_text(encoding="utf-8")
            out_content = out_file.read_text(encoding="utf-8") if out_file.exists() else ""
            testcases.append(
                TestCase(
                    id=idx_str,
                    input=in_content,
                    output=out_content,
                    kind=TestCaseKind.SAMPLE,
                )
            )

    # 2. Look for tests in .cph/ if tests/ was empty
    if not testcases:
        cph_dir = prob_dir / ".cph"
        if cph_dir.exists():
            for prob_file in cph_dir.glob("*.prob"):
                try:
                    data = json.loads(prob_file.read_text(encoding="utf-8"))
                    for i, t in enumerate(data.get("tests", []), 1):
                        testcases.append(
                            TestCase(
                                id=i,
                                input=t.get("input", ""),
                                output=t.get("expectedOutput", ""),
                                kind=TestCaseKind.SAMPLE,
                            )
                        )
                except Exception:
                    continue

    if not testcases:
        console.print(
            f"[bold yellow]No test cases found in {tests_dir} or {prob_dir / '.cph'}[/bold yellow]"
        )
        return 1

    results = execute_and_render_tests(
        source_path, testcases, time_limit_ms=args.time_limit
    )
    all_pass = all(r.status == "PASS" for r in results)
    return 0 if all_pass else 1


def cmd_push(args: argparse.Namespace) -> int:
    """Push a problem to CPH via HTTP."""
    target = Path(args.target).resolve()
    if target.is_dir():
        prob_json = target / "problem.json"
    else:
        prob_json = target

    if not prob_json.exists():
        console.print(f"[bold red]Error: Problem specification not found at {prob_json}[/bold red]")
        return 1

    try:
        spec_data = json.loads(prob_json.read_text(encoding="utf-8"))
        spec = ProblemSpec.model_validate(spec_data)
        res = dispatch_to_cph(spec, ports=[args.port] if args.port else None)
        if res["success"]:
            console.print(f"[bold green]✔ {res['message']}[/bold green]")
            return 0
        else:
            console.print(f"[bold red]✘ {res['message']}[/bold red]")
            return 1
    except Exception as e:
        console.print(f"[bold red]Error parsing problem json:[/bold red] {e}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="harpy",
        description="Harpy: AI-assisted competitive programming & interview prep toolkit",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Test runner
    test_parser = subparsers.add_parser("test", help="Test a solution against test cases")
    test_parser.add_argument("solution", help="Path to solution file (e.g., solution.cpp)")
    test_parser.add_argument(
        "--time-limit",
        type=int,
        default=2000,
        help="Time limit per test in milliseconds (default: 2000)",
    )

    # CPH push
    push_parser = subparsers.add_parser("push", help="Push a problem to CPH HTTP listener")
    push_parser.add_argument("target", help="Directory or problem.json to push")
    push_parser.add_argument("--port", type=int, help="Target CPH listener port")

    args = parser.parse_args()

    if args.command == "test":
        return cmd_test(args)
    elif args.command == "push":
        return cmd_push(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
