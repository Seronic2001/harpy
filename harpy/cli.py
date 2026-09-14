from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure UTF-8 output streams even in piped/isolated environments (Windows CI, agent subshells)
for _s in ("stdout", "stderr", "stdin"):
    _stream = getattr(sys, _s, None)
    if _stream and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from rich.console import Console
from rich.panel import Panel
from harpy import __version__
from harpy.cph import dispatch_to_cph, write_cph_file
from harpy.formatter import create_problem_workspace
from harpy.generator import (
    execute_test_generation_for_problem,
    find_problem_path,
    spawn_background_test_generation,
)
from harpy.models import ProblemSpec, TestCase, TestCaseKind
from harpy.oracle import execute_test_generator, verify_and_generate_testcases
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

    local commands="init create new test push generate-tests stress setup-ai completion mcp --help --version"

    if [ "$cword" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
        return 0
    fi

    case "${words[1]}" in
        create|new)
            local files=""
            for f in *.json; do
                if [ -f "$f" ]; then
                    files+="$f "
                fi
            done
            COMPREPLY=( $(compgen -W "$files" -- "$cur") )
            if [ ${#COMPREPLY[@]} -eq 0 ]; then
                COMPREPLY=( $(compgen -f -- "$cur") )
            fi
            return 0
            ;;
        test)
            local candidates=""
            # 1. Solution files in current directory
            for f in *.cpp *.cc *.cxx *.py *.java; do
                if [ -f "$f" ]; then
                    candidates+="$f "
                fi
            done
            # 2. Problem solution files and directories in problems/ (including categories)
            if [ -d "problems" ]; then
                for d in problems/* problems/*/*; do
                    if [ -d "$d" ]; then
                        candidates+="$d/ "
                        for f in "$d"/*.cpp "$d"/*.cc "$d"/*.cxx "$d"/*.py "$d"/*.java; do
                            if [ -f "$f" ]; then
                                candidates+="$(basename "$f") "
                                candidates+="$f "
                            fi
                        done
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
                for d in problems/* problems/*/*; do
                    if [ -d "$d" ]; then
                        dirs+="$(basename "$d") $d/ "
                    fi
                done
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
    - Direct path: "problems/dynamic-programming/maximum-subarray-sum/maximum-subarray-sum.cpp"
    - Filename only: "maximum-subarray-sum.cpp"
    - Problem slug: "maximum-subarray-sum"
    - Category + slug: "dynamic-programming/maximum-subarray-sum"
    - Directory: "problems/dynamic-programming/maximum-subarray-sum"
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

    # 3. Check under problems/, current dir, and all category subdirectories
    bases = [Path("problems"), Path(".")]
    if Path("problems").exists():
        for cat in Path("problems").iterdir():
            if cat.is_dir():
                bases.append(cat)

    for base in bases:
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

    # 4. Search recursively inside problems/
    if Path("problems").exists():
        clean_q = query.replace(".cpp", "").replace(".py", "")
        # First exact file stem match in any subfolder
        for match in Path("problems").rglob(f"{clean_q}.*"):
            if match.is_file() and match.suffix in (".cpp", ".py", ".java"):
                return match.resolve()
        # Then exact directory match
        for d in Path("problems").rglob(f"{clean_q}"):
            if d.is_dir():
                for ext in ("*.cpp", "*.py", "*.java"):
                    matches = list(d.glob(ext))
                    if matches:
                        return matches[0].resolve()
        # Finally fuzzy match
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
            for item in sorted(Path("problems").iterdir()):
                if item.is_dir():
                    children = [c for c in sorted(item.iterdir()) if c.is_dir()]
                    if (item / "problem.json").exists() or any(item.glob("*.cpp")):
                        console.print(f"  • {item.name}")
                    elif children:
                        console.print(f"  [cyan][{item.name}][/cyan]")
                        for cp in children:
                            console.print(f"    • {cp.name}")
                    else:
                        console.print(f"  • {item.name}")
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
                    cph_data = json.loads(prob_file.read_text(encoding="utf-8"))
                    for idx, test_dict in enumerate(cph_data.get("tests", []), 1):
                        testcases.append(
                            TestCase(
                                id=idx,
                                input=test_dict.get("input", ""),
                                output=test_dict.get("output", ""),
                                kind=TestCaseKind.SAMPLE,
                            )
                        )
                except Exception:
                    pass

    if not testcases:
        console.print(f"[bold red]Error: No test cases found in {tests_dir} or {prob_dir / '.cph'}[/bold red]")
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
        # Check inside problems/ directly
        alt = Path("problems") / args.target / "problem.json"
        if alt.exists():
            prob_json = alt
        elif Path("problems").exists():
            # Check inside category subfolders
            found = list(Path("problems").rglob(f"{args.target}/problem.json"))
            if found:
                prob_json = found[0]
            else:
                console.print(f"[bold red]Error: Problem specification not found at {prob_json}[/bold red]")
                return 1
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


def cmd_create(args: argparse.Namespace) -> int:
    """Create and scaffold a competitive programming problem workspace from a JSON specification or CLI arguments."""
    spec_target = getattr(args, "spec_opt", None) or getattr(args, "spec_pos", None)

    spec_data: dict = {}
    if spec_target == "-":
        try:
            raw = sys.stdin.read()
            if not raw.strip():
                console.print("[bold red]Error: Received empty input from stdin.[/bold red]")
                return 1
            spec_data = json.loads(raw)
        except Exception as e:
            console.print(f"[bold red]Error reading JSON from stdin:[/bold red] {e}")
            return 1
    elif spec_target:
        p = Path(spec_target)
        if not p.is_file():
            console.print(f"[bold red]Error: Specification file not found:[/bold red] {spec_target}")
            return 1
        try:
            spec_data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            console.print(f"[bold red]Error reading JSON from {spec_target}:[/bold red] {e}")
            return 1
    elif not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                spec_data = json.loads(raw)
        except Exception:
            pass

    # CLI flag overrides
    if getattr(args, "title", None):
        spec_data["title"] = args.title
    if getattr(args, "category", None):
        spec_data["category"] = args.category
    if getattr(args, "difficulty", None) and ("difficulty" not in spec_data or args.difficulty != "Medium"):
        spec_data["difficulty"] = args.difficulty
    if getattr(args, "tags", None):
        spec_data["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]

    if getattr(args, "oracle", None):
        oracle_path = Path(args.oracle)
        if oracle_path.is_file():
            spec_data["reference_code"] = oracle_path.read_text(encoding="utf-8")
        else:
            console.print(f"[bold red]Error: Oracle script not found:[/bold red] {args.oracle}")
            return 1

    if getattr(args, "generator", None):
        gen_path = Path(args.generator)
        if gen_path.is_file():
            spec_data["test_generator"] = gen_path.read_text(encoding="utf-8")
        else:
            console.print(f"[bold red]Error: Test generator script not found:[/bold red] {args.generator}")
            return 1

    if not spec_data.get("title"):
        console.print("[bold red]Error: Problem title is required (provide in spec JSON or with --title).[/bold red]")
        return 1

    try:
        spec = ProblemSpec.model_validate(spec_data)
    except Exception as e:
        console.print(f"[bold red]Error validating ProblemSpec:[/bold red] {e}")
        return 1

    is_async = getattr(args, "async_mode", False) or bool(spec_data.get("async", False))
    is_sync = getattr(args, "sync_mode", False)
    async_mode = is_async and not is_sync

    # 1. Collect inputs / run tests
    if async_mode:
        # Instant Scaffolding Mode:
        # Only verify immediate sample cases if their output is missing
        if spec.reference_code and spec.testcases:
            unverified = [tc for tc in spec.testcases if not tc.output]
            if unverified:
                try:
                    sample_inputs = [(tc.normalized_input(), tc.kind, tc.explanation) for tc in unverified]
                    verified = verify_and_generate_testcases(
                        spec.reference_code, sample_inputs, timeout_sec=3.0
                    )
                    # Replace unverified outputs
                    v_map = {tc.normalized_input().strip(): tc.output for tc in verified}
                    for tc in spec.testcases:
                        if not tc.output and tc.normalized_input().strip() in v_map:
                            tc.output = v_map[tc.normalized_input().strip()]
                except Exception as e:
                    console.print(f"[bold yellow]Warning: Quick sample verification failed: {e}[/bold yellow]")
    else:
        # Synchronous Mode: Full generation and verification
        raw_inputs = [
            (tc.normalized_input(), tc.kind, tc.explanation)
            for tc in spec.testcases
        ]

        if spec.test_generator:
            try:
                console.print("[cyan]Running Python algorithmic test generator...[/cyan]")
                generated_inputs = execute_test_generator(spec.test_generator)
                console.print(f"[bold green]✔ Generated {len(generated_inputs)} test cases programmatically.[/bold green]")
                raw_inputs.extend(generated_inputs)
            except Exception as e:
                console.print(f"[bold red]Test generator failed:[/bold red] {e}")
                return 1

        if spec.reference_code and raw_inputs:
            try:
                console.print("[cyan]Running Python reference oracle across test cases...[/cyan]")
                verified_cases = verify_and_generate_testcases(
                    spec.reference_code, raw_inputs, timeout_sec=float(spec.time_limit_ms) / 1000.0 + 2.0
                )
                spec.testcases = verified_cases
                console.print(f"[bold green]✔ Verified {len(verified_cases)} total test cases with reference oracle.[/bold green]")
            except Exception as e:
                console.print(f"[bold red]Oracle verification failed:[/bold red] {e}")
                return 1
        elif raw_inputs and not spec.testcases:
            spec.testcases = [
                TestCase(id=idx, input=inp, output="", kind=kind, explanation=expl)
                for idx, (inp, kind, expl) in enumerate(raw_inputs, 1)
            ]

    # 2. Create problem workspace
    lang = getattr(args, "lang", "cpp") or "cpp"
    base_dir = getattr(args, "base_dir", ".") or "."

    import shutil
    if lang == "cpp" and not (shutil.which("g++") or shutil.which("clang++")):
        console.print(
            "[bold yellow]Note:[/bold yellow] No C++ compiler ('g++' or 'clang++') detected in PATH. "
            "[dim]Tip: You can use Python with '--lang py' to generate and test without a C++ compiler.[/dim]"
        )

    ws = create_problem_workspace(
        spec,
        base_dir=base_dir,
        category=spec.category,
        lang=lang,
    )

    # 3. Write offline CPH file
    write_cph_file(spec, ws["solution"])

    # 4. Dispatch to CPH if requested
    cph_status = "[dim]offline .cph created[/dim]"
    if not getattr(args, "no_cph", False):
        res = dispatch_to_cph(spec, ports=[args.port] if getattr(args, "port", None) else None)
        if res.get("success"):
            cph_status = f"[bold green]✔ Synced with CPH ({res.get('port')})[/bold green]"
        else:
            cph_status = "[dim]CPH listener not active (offline .cph configured)[/dim]"

    # 5. Handle Background Test Generation if async
    bg_info = ""
    if async_mode and spec.test_generator:
        try:
            bg_pid = spawn_background_test_generation(ws["dir"], debug=getattr(args, "debug", False))
            bg_info = f"\n[bold magenta]⚡ Background Generator:[/bold magenta] Active (PID {bg_pid}) - synthesizing stress/edge tests"
        except Exception as e:
            bg_info = f"\n[bold yellow]Background generator warning:[/bold yellow] {e}"

    # 6. Output Rich panel
    category_name = spec.get_category()
    slug = spec.get_slug()
    rel_sol = ws["solution"]
    try:
        rel_sol = rel_sol.relative_to(Path.cwd())
    except ValueError:
        pass

    rel_md = ws["markdown"]
    try:
        rel_md = rel_md.relative_to(Path.cwd())
    except ValueError:
        pass

    summary_text = (
        f"[bold]Title:[/bold] {spec.title}\n"
        f"[bold]Category:[/bold] [yellow]{category_name}[/yellow]\n"
        f"[bold]Difficulty:[/bold] {spec.difficulty}\n"
        f"[bold]Specification:[/bold] [link=file://{ws['markdown'].resolve()}]{rel_md}[/link]\n"
        f"[bold]Starter Code:[/bold] [link=file://{ws['solution'].resolve()}]{rel_sol}[/link]\n"
        f"[bold]Test Cases:[/bold] {len(spec.testcases)} cases in {ws['tests_dir'].name}/\n"
        f"[bold]CPH Integration:[/bold] {cph_status}"
        f"{bg_info}\n\n"
        f"⚡ [bold green]Ready to solve![/bold green] Run: [bold cyan]harpy test {slug}[/bold cyan]"
    )

    console.print(Panel(
        summary_text,
        title=f"🚀 Problem Created: [bold cyan]{slug}[/bold cyan]",
        expand=False,
    ))
    return 0


def cmd_generate_tests(args: argparse.Namespace) -> int:
    """Run test generator & reference oracle to synthesize test cases for an existing problem."""
    target = getattr(args, "problem", ".") or "."
    prob_path = find_problem_path(target)
    if not prob_path:
        console.print(f"[bold red]Error: Could not locate problem directory for:[/bold red] {target}")
        return 1

    oracle_code = None
    gen_code = None

    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                data = json.loads(raw)
                oracle_code = data.get("reference_code")
                gen_code = data.get("test_generator")
        except Exception:
            pass

    if getattr(args, "oracle", None):
        p = Path(args.oracle)
        if p.is_file():
            oracle_code = p.read_text(encoding="utf-8")
        else:
            console.print(f"[bold red]Error: Oracle file not found:[/bold red] {args.oracle}")
            return 1

    if getattr(args, "generator", None):
        p = Path(args.generator)
        if p.is_file():
            gen_code = p.read_text(encoding="utf-8")
        else:
            console.print(f"[bold red]Error: Generator file not found:[/bold red] {args.generator}")
            return 1

    if getattr(args, "async_mode", False):
        pid = spawn_background_test_generation(prob_path, debug=getattr(args, "debug", False))
        console.print(f"[bold green]✔ Spawned background test generator (PID {pid}) for:[/bold green] {prob_path.name}")
        return 0

    console.print("[cyan]Running test generator and reference oracle...[/cyan]")
    count, msg = execute_test_generation_for_problem(
        prob_path,
        oracle_code=oracle_code,
        generator_code=gen_code,
    )
    if count > 0:
        console.print(f"[bold green]✔ {msg}[/bold green]")
        return 0
    else:
        if "already exist" in msg:
            console.print(f"[bold green]✔ {msg}[/bold green]")
            return 0
        console.print(f"[bold red]✘ {msg}[/bold red]")
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


DEFAULT_SKILL_CONTENT = """---
name: harpy-cp
description: Formulates algorithm problems from uploaded images or raw text into LeetCode-style markdown specifications, generates verified test cases using a Python reference oracle, creates a starter <problem_slug>.cpp (or .py) file with an empty solve(...) function with prefilled parameters for the user to implement, syncs with CPH, and tests solutions.
---

# Harpy Competitive Programming Workflow

Follow this procedure whenever the user:
- Uploads an image, screenshot, whiteboard photo, or text of a coding/algorithm problem into chat.
- Asks to set up a problem in C++ or Python.

---

## ⚠️ Critical Rules & Constraints (Zero Latency)

1. ⛔ **NEVER SEARCH THE WEB**:
   - Do **NOT** use web search or browse online for the problem statement.
   - Most interview and OA questions are proprietary, recent, or modified.
   - Web searches waste multiple agent turns, trigger permission dialogs, and cause significant latency.
   - Formulate everything directly from the user's provided image, screenshot, or text.

2. ⛔ **NO PRE-FLIGHT EXPLORATION OR SCRATCH PRE-TESTING**:
   - Do **NOT** run exploratory commands like `which harpy`, `find`, `ls`, `harpy --help`, or `harpy init`.
   - Do **NOT** run `list_dir` on workspace or `problems/`.
   - Do **NOT** run `view_file` on active documents from metadata or MCP schema files.
   - Do **NOT** write temporary scripts in `scratch/` to manually test the Python oracle first.
   - Execute `harpy create` in your **VERY FIRST TURN**.

3. ⛔ **NO REDUNDANT C++ REFERENCE SOLVERS**:
   - Do **NOT** write, compile, or run a C++ reference solver.
   - The Python reference oracle (`reference_code`) inside the specification automatically executes across all test cases and generates authoritative expected outputs with zero compilation overhead.

4. ⛔ **USER IMPLEMENTS `solve(...)` (LeetCode-style)**:
   - For C++ (`<problem_slug>.cpp`), fast I/O is handled in `main()` which passes typed arguments to `solve(...)`.
   - For Python (`<problem_slug>.py`), input reading and fast I/O are handled in `main()` which passes typed arguments to `solve(...)` and prints the result.
   - Supply `cpp_signature` + `cpp_main_parser` for C++, OR `py_signature` + `py_main_parser` for Python.
   - **NEVER implement the algorithmic logic inside `solve(...)`**. The user writes their own algorithm.

5. 💡 **LANGUAGE SELECTION & ZERO-TURN COMPILER HANDLING**:
   - If the user explicitly asks for Python, or if you are on Windows without a pre-installed `g++`/`clang++`, use `--lang py` with `py_signature` and `py_main_parser`.
   - Otherwise default to C++ (`cpp`) with `cpp_signature` and `cpp_main_parser`.
   - Do NOT run exploratory commands to check compilers. Make the language decision immediately.

6. ⛔ **DO NOT VIEW GENERATED FILES AFTER `harpy create`**:
   - Do **NOT** open or `cat` the generated `.cpp`, `.py`, `problem.md`, or test files after scaffolding.
   - `harpy create` already prints a full summary of what was created and any oracle errors.
   - Viewing files wastes an entire agent turn for zero new information.

---

## ⚡ Direct 1-Turn Setup: Pipe JSON to `harpy create -`

Do not create intermediate scratch files. Execute problem setup in **a single terminal command**.

> [!IMPORTANT]
> **Detect the shell FIRST.** Bash heredocs (`<< 'EOF'`) do NOT work in PowerShell.
> - **Linux / macOS / Git Bash / WSL**: Use `<< 'EOF'` heredoc.
> - **Windows PowerShell / pwsh**: Use the PowerShell `@'...'@` here-string.

### C++ Problem Setup:
```bash
harpy create --async - << 'EOF'
{
  "title": "Lexicographically Minimal Walk",
  "category": "graph-algorithms",
  "difficulty": "Medium",
  "tags": ["Graph", "BFS", "Shortest Path"],
  "description": "Given a directed graph with characters on edges, find the lexicographically smallest path...",
  "input_format": "The first line contains N and M...",
  "output_format": "Print the string formed by the walk...",
  "constraints": ["$1 \\le N, M \\le 10^5$"],
  "cpp_signature": "string solve(int n, int m, int k, const vector<vector<pair<int, char>>>& adj)",
  "cpp_main_parser": "int n, m, k;\\ncin >> n >> m >> k;\\nvector<vector<pair<int, char>>> adj(n + 1);\\nfor (int i = 0; i < m; ++i) {\\n    int u, v; char c;\\n    cin >> u >> v >> c;\\n    adj[u].push_back({v, c});\\n}\\ncout << solve(n, m, k, adj) << \\\"\\\\n\\\";",
  "testcases": [{"input": "4 4 2\\n1 2 a\\n2 4 b\\n1 3 a\\n3 4 a\\n", "kind": "sample"}],
  "reference_code": "import sys\\ndef solve():\\n    ...\\nsolve()\\n",
  "test_generator": "def generate():\\n    yield ('1 0 1\\\\n', 'edge')\\n"
}
EOF
```

### Python Problem Setup (with LeetCode I/O Support):
```bash
harpy create --lang py --async - << 'EOF'
{
  "title": "Lexicographically Minimal Walk",
  "category": "graph-algorithms",
  "difficulty": "Medium",
  "tags": ["Graph", "BFS", "Shortest Path"],
  "description": "Given a directed graph with characters on edges, find the lexicographically smallest path...",
  "input_format": "The first line contains N and M...",
  "output_format": "Print the string formed by the walk...",
  "constraints": ["$1 \\le N, M \\le 10^5$"],
  "py_signature": "def solve(n: int, m: int, k: int, adj: list[list[tuple[int, str]]]) -> str",
  "py_main_parser": "import sys\\ninput_data = sys.stdin.read().split()\\nif not input_data: return\\nn, m, k = map(int, input_data[:3])\\n...\\nprint(solve(n, m, k, adj))",
  "testcases": [{"input": "4 4 2\\n1 2 a\\n2 4 b\\n1 3 a\\n3 4 a\\n", "kind": "sample"}],
  "reference_code": "import sys\\ndef solve():\\n    ...\\nsolve()\\n",
  "test_generator": "def generate():\\n    yield ('1 0 1\\\\n', 'edge')\\n"
}
EOF
```
*(On Windows PowerShell, replace `<< 'EOF' ... EOF` with `@' ... '@ | harpy create ... -`)*

> [!TIP]
> **Sub-Second Scaffolding with `--async`**:
> Using `--async` scaffolds the workspace, writes the starter code file, and registers the sample test cases in CPH in **under 0.2 seconds** so the user can start coding immediately.
> In the background, Harpy automatically synthesizes stress/edge cases from `test_generator`, verifies them with `reference_code` using the fast single-process batch oracle, and appends them to CPH and `tests/`!

#### CSES Categories:
Classify into one of the 12 standard CSES categories:
- `dynamic-programming` (knapsack, LIS, grid DP)
- `graph-algorithms` (BFS, DFS, Dijkstra, flows)
- `tree-algorithms` (tree traversals, LCA, diameter)
- `sorting-and-searching` (binary search, two pointers)
- `greedy-algorithms` (intervals, scheduling)
- `range-queries` (segment tree, Fenwick, prefix sums)
- `mathematics` (number theory, combinatorics, modular arithmetic)
- `string-algorithms` (hashing, KMP, trie)
- `geometry` (convex hull, polygon)
- `bit-manipulation` (bitmasks, XOR)
- `introductory-problems` (simulation, basic loops)
- `advanced-techniques`

**What `harpy create` automatically accomplishes in this 1 step:**
1. Runs the Python `reference_code` across all test cases to verify and generate exact outputs.
2. Scaffolds `problems/<category>/<slug>/` containing:
   - `problem.md` (LeetCode specification with LaTeX formulas)
   - `<slug>.cpp` or `<slug>.py` (Starter code with typed signature / starter template)
   - `tests/in_*.txt` & `tests/out_*.txt`
   - `problem.json`
3. Writes `.cph/.<slug>.<ext>_<hash>.prob` for offline testing.
4. Attempts HTTP sync with active CPH extension listener on port 27121.

---

## 3. Present to the User
Report:
- Summary of the problem, category, and constraints.
- Direct clickable link to starter file: [`problems/<category>/<slug>/<slug>.<ext>`](file://problems/<category>/<slug>/<slug>.<ext>).
- Summary of verified test cases (sample, edge, stress).
- The exact test command:
  ```bash
  harpy test <slug>
  ```
  *(Harpy CLI automatically searches across all category folders and handles both C++ and Python).*

---

## 4. Testing the User's Solution
When the user says "test my code", "run tests", or asks for debugging:
1. Run `harpy test <slug>`.
2. Display the Rich test results (PASS / FAIL / TLE / RTE) and explain any failures if requested.
"""


def cmd_setup_ai(args: argparse.Namespace) -> int:
    """Setup Harpy AI skill and MCP configuration for Antigravity, Cursor, and Claude Desktop."""
    home = Path.home()
    
    # 1. Locate or read bundled skill, falling back to embedded default
    bundled_skill_path = Path(__file__).resolve().parent.parent / "skills" / "harpy-cp" / "SKILL.md"
    if bundled_skill_path.exists():
        skill_content = bundled_skill_path.read_text(encoding="utf-8")
    else:
        skill_content = DEFAULT_SKILL_CONTENT

    # 2. Install skill to Antigravity global config
    gemini_skills_dir = home / ".gemini" / "config" / "skills" / "harpy-cp"
    gemini_skills_dir.mkdir(parents=True, exist_ok=True)
    (gemini_skills_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")
    console.print(f"[bold green]✔ Installed Antigravity skill to:[/bold green] {gemini_skills_dir / 'SKILL.md'}")

    # 3. Configure or update ~/.gemini/config/mcp_config.json
    mcp_config_path = home / ".gemini" / "config" / "mcp_config.json"
    mcp_config: dict = {}
    if mcp_config_path.exists():
        try:
            mcp_config = json.loads(mcp_config_path.read_text(encoding="utf-8"))
        except Exception:
            mcp_config = {}

    mcp_servers = mcp_config.setdefault("mcpServers", {})

    import shutil
    harpy_exe = shutil.which("harpy")
    if harpy_exe and not harpy_exe.endswith("python"):
        server_cmd = harpy_exe
        server_args = ["mcp"]
    else:
        python_exe = (
            shutil.which("python3")
            or shutil.which("python")
            if getattr(sys, "frozen", False)
            else sys.executable
        )
        server_cmd = python_exe
        server_args = ["-m", "harpy.mcp_server"]

    mcp_servers["harpy"] = {
        "command": server_cmd,
        "args": server_args,
    }
    mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_config_path.write_text(json.dumps(mcp_config, indent=2), encoding="utf-8")
    console.print(f"[bold green]✔ Registered MCP server in:[/bold green] {mcp_config_path}")

    # 4. Print MCP snippet for Claude Desktop and Cursor
    cursor_snippet = json.dumps({
        "mcpServers": {
            "harpy": {
                "command": server_cmd,
                "args": server_args,
            }
        }
    }, indent=2)

    console.print(Panel(
        f"[bold cyan]Cursor & Claude Desktop Configuration[/bold cyan]\n\n"
        f"Add the following to your [yellow]claude_desktop_config.json[/yellow] or [yellow].cursor/mcp.json[/yellow]:\n\n"
        f"[green]{cursor_snippet}[/green]",
        title="🤖 AI Integration",
        expand=False
    ))

    if not shutil.which("harpy"):
        console.print(
            "\n[yellow]💡 Note:[/yellow] If 'harpy' is not recognized in your terminal yet, you can run any command using:"
            "\n   [bold green]python -m harpy <command>[/bold green] (or [bold green]py -m harpy <command>[/bold green] on Windows)\n"
        )

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="harpy",
        description="Harpy: AI-assisted competitive programming & interview prep toolkit",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging (creates .generator.log)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Init workspace
    subparsers.add_parser("init", help="Initialize current folder for DSA practice with Harpy")

    # Create problem
    create_parser = subparsers.add_parser(
        "create",
        aliases=["new"],
        help="Create and scaffold a problem from a JSON specification or flags",
    )
    create_parser.add_argument(
        "spec_pos",
        nargs="?",
        default=None,
        help="Path to problem_spec.json (or '-' for stdin)",
    )
    create_parser.add_argument(
        "-s",
        "--spec",
        dest="spec_opt",
        help="Path to problem_spec.json (or '-' for stdin)",
    )
    create_parser.add_argument("--title", help="Problem title")
    create_parser.add_argument(
        "--category", help="CSES category (e.g. dynamic-programming, graph-algorithms)"
    )
    create_parser.add_argument(
        "--difficulty", default="Medium", help="Difficulty (Easy/Medium/Hard)"
    )
    create_parser.add_argument("--tags", help="Comma-separated topics/tags")
    create_parser.add_argument("--oracle", help="Path to Python reference solver script")
    create_parser.add_argument(
        "-g", "--generator", help="Path to Python script containing algorithmic test generator"
    )
    create_parser.add_argument("--lang", default="cpp", help="Starter code language (cpp/py)")
    create_parser.add_argument("--base-dir", default=".", help="Base directory for problems")
    create_parser.add_argument(
        "-b",
        "--async",
        dest="async_mode",
        action="store_true",
        help="Scaffold problem instantly (<0.2s) and synthesize tests in the background",
    )
    create_parser.add_argument(
        "--sync",
        dest="sync_mode",
        action="store_true",
        help="Wait synchronously for test generation and oracle verification to complete",
    )
    create_parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging"
    )
    create_parser.add_argument(
        "--no-cph", action="store_true", help="Skip dispatching to CPH listener"
    )
    create_parser.add_argument("--port", type=int, help="Target CPH listener port")

    # Generate tests / stress
    gen_parser = subparsers.add_parser(
        "generate-tests",
        aliases=["stress"],
        help="Synthesize test cases via algorithmic generator & reference oracle",
    )
    gen_parser.add_argument(
        "problem",
        nargs="?",
        default=".",
        help="Problem slug or directory path (default: current directory)",
    )
    gen_parser.add_argument(
        "-b",
        "--async",
        dest="async_mode",
        action="store_true",
        help="Run generation in the background",
    )
    gen_parser.add_argument(
        "--debug", action="store_true", help="Enable verbose debug logging"
    )
    gen_parser.add_argument("--oracle", help="Path to reference python solver")
    gen_parser.add_argument(
        "-g", "--generator", help="Path to test generator python script"
    )

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

    # Setup AI & MCP
    subparsers.add_parser("setup-ai", help="Configure Harpy AI skill and MCP server for Antigravity, Cursor, and Claude")

    # Run MCP stdio server directly
    subparsers.add_parser("mcp", help="Run Harpy MCP stdio server")

    args = parser.parse_args()

    if args.command in ("create", "new"):
        return cmd_create(args)
    elif args.command in ("generate-tests", "stress"):
        return cmd_generate_tests(args)
    elif args.command == "init":
        return cmd_init(args)
    elif args.command == "test":
        return cmd_test(args)
    elif args.command == "push":
        return cmd_push(args)
    elif args.command == "completion":
        return cmd_completion(args)
    elif args.command == "setup-ai":
        return cmd_setup_ai(args)
    elif args.command == "mcp":
        try:
            from harpy.mcp_server import main as mcp_main
        except ImportError:
            console.print("[bold red]Error:[/bold red] The 'mcp' Python package is required. Install with: pip install 'harpy-cp[mcp]'")
            return 1
        mcp_main()
        return 0
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
