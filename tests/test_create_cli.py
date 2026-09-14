import json
import sys
from pathlib import Path
import pytest
from harpy.cli import main
from harpy.models import ProblemSpec


def test_cli_create_from_file(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    spec_dict = {
        "title": "Min Cost Climbing Stairs",
        "category": "dynamic-programming",
        "difficulty": "Easy",
        "tags": ["Dynamic Programming"],
        "description": "Calculate minimum cost to reach top of stairs.",
        "testcases": [
            {"input": "3\n10 15 20\n", "output": "15\n", "kind": "sample"}
        ],
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec_dict), encoding="utf-8")

    # Mock CPH dispatch
    monkeypatch.setattr(
        "harpy.cli.dispatch_to_cph",
        lambda s, ports=None: {"success": False, "message": "No CPH listener"},
    )

    sys.argv = ["harpy", "create", "-s", str(spec_file)]
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert "Min Cost Climbing Stairs" in captured.out
    assert "dynamic-programming" in captured.out

    prob_dir = tmp_path / "problems" / "dynamic-programming" / "min-cost-climbing-stairs"
    assert prob_dir.is_dir()
    assert (prob_dir / "min-cost-climbing-stairs.cpp").is_file()
    assert (prob_dir / "problem.md").is_file()
    assert (prob_dir / "problem.json").is_file()
    assert (prob_dir / "tests" / "in_01.txt").is_file()
    assert (prob_dir / ".cph").is_dir()


def test_cli_create_with_oracle(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    # Reference code computes sum of two numbers
    ref_code = """
import sys
lines = sys.stdin.read().split()
if lines:
    a, b = int(lines[0]), int(lines[1])
    print(a + b)
"""

    spec_dict = {
        "title": "Addition Oracle Test",
        "category": "introductory-problems",
        "reference_code": ref_code,
        "testcases": [
            {"input": "3 5\n", "output": "", "kind": "sample"},
            {"input": "100 250\n", "output": "", "kind": "edge"},
        ],
    }
    spec_file = tmp_path / "addition.json"
    spec_file.write_text(json.dumps(spec_dict), encoding="utf-8")

    monkeypatch.setattr(
        "harpy.cli.dispatch_to_cph",
        lambda s, ports=None: {"success": False, "message": "No listener"},
    )

    sys.argv = ["harpy", "create", str(spec_file)]
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert "Verified 2 total test cases with reference oracle" in captured.out

    prob_dir = tmp_path / "problems" / "introductory-problems" / "addition-oracle-test"
    assert (prob_dir / "tests" / "out_01.txt").read_text().strip() == "8"
    assert (prob_dir / "tests" / "out_02.txt").read_text().strip() == "350"


def test_cli_create_from_stdin(tmp_path: Path, monkeypatch, capsys):
    import io

    monkeypatch.chdir(tmp_path)

    spec_dict = {
        "title": "Piped Problem",
        "category": "sorting-and-searching",
        "testcases": [{"input": "1\n", "output": "1\n"}],
    }

    monkeypatch.setattr(
        "harpy.cli.dispatch_to_cph",
        lambda s, ports=None: {"success": False, "message": "No listener"},
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(spec_dict)))

    sys.argv = ["harpy", "create", "-"]
    code = main()
    assert code == 0

    prob_dir = tmp_path / "problems" / "sorting-and-searching" / "piped-problem"
    assert prob_dir.is_dir()
    assert (prob_dir / "piped-problem.cpp").is_file()


def test_cli_create_errors(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    # Missing file
    sys.argv = ["harpy", "create", "-s", "nonexistent.json"]
    assert main() == 1

    # Empty title
    spec_file = tmp_path / "invalid.json"
    spec_file.write_text("{}", encoding="utf-8")
    sys.argv = ["harpy", "create", "-s", str(spec_file)]
    assert main() == 1
