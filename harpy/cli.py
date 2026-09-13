from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from harpy import __version__
from harpy.cph import dispatch_to_cph, write_cph_file
from harpy.formatter import create_problem_workspace
from harpy.models import ProblemSpec, TestCase, TestCaseKind
from harpy.oracle import verify_and_generate_testcases
from harpy.runner import execute_and_render_tests


console = Console()


BASH_COMPLETION_SCRIPT = """# bash completion for harpy
_harpy_completions()
{
    local cur prev words cword
    if declare -F _init_completion >/dev/null 2>&1; then
        _init_completion || return
    else
        cur="${COMP_WORDS[COMP_CWORD]}"
        prev="${COMP_WORDS[COMP_CWORD-1]}"
        words=("${COMP_WORDS[@]}")
        cword=$COMP_CWORD
    fi

    local commands="init test push completion --help --version"

    if [ "$cword" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    case "${words[1]}" in
        test)
            local candidates=""
            # Add files ending in cpp, py, java
            candidates+="$(compgen -f -X '!*.@(cpp|cc|cxx|py|java)' -- "$cur") "
            # Add problem names and problem files from problems/
            if [ -d "problems" ]; then
                for d in problems/*; do
                    if [ -d "$d" ]; then
                        local slug=$(basename "$d")
                        candidates+="$slug "
                        candidates+="$(ls "$d"/*.cpp "$d"/*.py 2>/dev/null) "
                    fi
                done
            fi
            COMPREPLY=( $(compgen -W "$candidates" -- "$cur") )
            if [ ${#COMPREPLY[@]} -eq 0 ]; then
                COMPREPLY=( $(compgen -f -- "$cur") )
            fi
            return 0
            ;;
        push)
            local dirs=""
            if [ -d "problems" ]; then
                dirs="$(ls -d problems/*/ 2>/dev/null)"
            fi
            COMPREPLY=( $(compgen -W "$dirs" -- "$cur") $(compgen -d -- "$cur") )
            return 0
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh install" -- "$cur") )
            return 0
            ;;
        *)
            COMPREPLY=( $(compgen -f -- "$cur") )
            return 0
            ;;
    esac
}
complete -F _harpy_completions harpy
"""


def find_solution_file(query: str) -> Optional[Path]:
    """
    Intelligently resolves a solution file from user input:
    - Direct path: "problems/two-sum/solution.cpp"
    - Filename only: "lexicographically-minimal-walk.cpp"
    - Problem slug: "lexicographically-minimal-walk"
    - Directory: "problems/lexicographically-minimal-walk"
    """
    p = Path(query)

    # 1. Exact file match
    if p.is_file():
        return p.resolve()

    # 2. Directory match
    if p.is_dir():
        for ext in ("*.cpp", "*.py", "*.java"):
            matches = list(p.glob(ext))
            if matches:
                return matches[0].resolve()

    # 3. Check under problems/
    for base in (Path("problems"), Path(".")):
        candidates = [
            base / query,
            base / f"{query}.cpp",
            base / f"{query}.py",
            base / query / f"{query}.cpp",
            base / query / "solution.cpp",
            base / query / f"{query}.py",
            base / query / "solution.py",
        ]
        for c in candidates:
            if c.is_file():
                return c.resolve()

    # 4. Fuzzy match inside problems/
    if Path("problems").exists():
        clean_q = query.replace(".cpp", "").replace(".py", "")
        for match in Path("problems").rglob(f"*{clean_q}*"):
            if match.is_file() and match.suffix in (".cpp", ".py", ".java"):
                return match.resolve()

    return None


def cmd_test(args: argparse.Namespace) -> int:
    """Run tests against a solution file."""
    source_path = find_solution_file(args.solution)
    if not source_path:
        console.print(f"[bold red]Error: Could not find solution file for:[/bold red] {args.solution}")
        if Path("problems").exists():
            console.print("[dim]Available problems in ./problems/:[/dim]")
            for p in sorted(Path("problems").iterdir()):
                if p.is_dir():
                    console.print(f"  • {p.name}")
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
        # Check inside problems/
        alt = Path("problems") / args.target / "problem.json"
        if alt.exists():
            prob_json = alt
        else:
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


def cmd_completion(args: argparse.Namespace) -> int:
    """Generate or install shell completion script."""
    shell = args.shell.lower() if args.shell else "bash"

    if shell == "bash":
        sys.stdout.write(BASH_COMPLETION_SCRIPT)
        return 0
    elif shell == "install":
        # Write to ~/.local/share/bash-completion/completions/harpy
        comp_dir = Path.home() / ".local" / "share" / "bash-completion" / "completions"
        comp_dir.mkdir(parents=True, exist_ok=True)
        comp_file = comp_dir / "harpy"
        comp_file.write_text(BASH_COMPLETION_SCRIPT, encoding="utf-8")

        # Also ensure ~/.bashrc sources it
        bashrc = Path.home() / ".bashrc"
        source_line = f"[ -f {comp_file} ] && source {comp_file}"
        if bashrc.exists():
            content = bashrc.read_text(encoding="utf-8")
            if str(comp_file) not in content:
                with open(bashrc, "a", encoding="utf-8") as f:
                    f.write(f"\n# Harpy CLI tab completion\n{source_line}\n")

        console.print(f"[bold green]✔ Bash completion installed to:[/bold green] {comp_file}")
        console.print("[dim]Run `source ~/.bashrc` or restart your shell to activate.[/dim]")
        return 0
    else:
        console.print(f"[bold yellow]Unsupported shell: {shell}. Only 'bash' or 'install' is currently supported.[/bold yellow]")
        return 1


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a directory for DSA / competitive programming with Harpy."""
    cwd = Path.cwd()
    tabignore = cwd / ".tabignore"
    if not tabignore.exists():
        tabignore.write_text("*.cpp\n*.c\n*.h\n*.hpp\n", encoding="utf-8")

    antigravityignore = cwd / ".antigravityignore"
    if not antigravityignore.exists():
        antigravityignore.write_text("*.cpp\n*.c\n*.h\n*.hpp\n", encoding="utf-8")

    (cwd / "problems").mkdir(exist_ok=True)
    console.print(f"[bold green]✔ Initialized Harpy DSA workspace in:[/bold green] {cwd}")
    console.print("  • Created [cyan]problems/[/cyan] directory")
    console.print("  • Configured [cyan].tabignore[/cyan] (ghost suggestions disabled for C++)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="harpy",
        description="Harpy: AI-assisted competitive programming & interview prep toolkit",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Init workspace
    subparsers.add_parser("init", help="Initialize current folder for DSA practice with Harpy")

    # Test runner
    test_parser = subparsers.add_parser("test", help="Test a solution against test cases")
    test_parser.add_argument("solution", help="Solution file, problem slug, or directory")
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

    # Shell completion
    comp_parser = subparsers.add_parser("completion", help="Generate or install shell completion")
    comp_parser.add_argument("shell", nargs="?", default="install", choices=["bash", "install"], help="Action ('install' or 'bash')")

    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args)
    elif args.command == "test":
        return cmd_test(args)
    elif args.command == "push":
        return cmd_push(args)
    elif args.command == "completion":
        return cmd_completion(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
