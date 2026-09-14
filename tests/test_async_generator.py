import json
import time
from pathlib import Path
import pytest
from harpy.cli import main
from harpy.generator import (
    execute_test_generation_for_problem,
    find_problem_path,
)


def test_find_problem_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prob_dir = tmp_path / "problems" / "graph-algorithms" / "sample-graph"
    prob_dir.mkdir(parents=True)
    (prob_dir / "problem.json").write_text(json.dumps({"title": "Sample Graph", "slug": "sample-graph"}))

    # By relative path
    found = find_problem_path(prob_dir)
    assert found == prob_dir.resolve()

    # By slug
    found_slug = find_problem_path("sample-graph")
    assert found_slug == prob_dir.resolve()

    # By title
    found_title = find_problem_path("Sample Graph")
    assert found_title == prob_dir.resolve()


def test_execute_test_generation_for_problem(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    prob_dir = tmp_path / "problems" / "math" / "sum-problem"
    prob_dir.mkdir(parents=True)
    tests_dir = prob_dir / "tests"
    tests_dir.mkdir()

    # Initial problem with 1 sample
    (tests_dir / "in_01.txt").write_text("5\n")
    (tests_dir / "out_01.txt").write_text("10\n")

    spec = {
        "title": "Sum Problem",
        "slug": "sum-problem",
        "category": "math",
        "time_limit_ms": 1000,
        "memory_limit_mb": 256,
        "reference_code": "import sys\nx = int(sys.stdin.read().strip())\nprint(x * 2)\n",
        "test_generator": """
def generate():
    yield ('10\\n', 'sample')
    yield ('20\\n', 'edge')
""",
        "testcases": [
            {"id": 1, "input": "5\n", "output": "10\n", "kind": "sample"}
        ]
    }
    (prob_dir / "problem.json").write_text(json.dumps(spec, indent=2))
    (prob_dir / "sum-problem.cpp").write_text("// C++ solution")

    count, msg = execute_test_generation_for_problem(prob_dir)
    assert count == 2
    assert "Successfully generated and verified 2 test cases" in msg

    # Verify tests/ files
    assert (tests_dir / "in_02.txt").read_text().strip() == "10"
    assert (tests_dir / "out_02.txt").read_text().strip() == "20"
    assert (tests_dir / "in_03.txt").read_text().strip() == "20"
    assert (tests_dir / "out_03.txt").read_text().strip() == "40"

    # Verify problem.json has 3 cases
    updated_spec = json.loads((prob_dir / "problem.json").read_text())
    assert len(updated_spec["testcases"]) == 3

    # Verify .cph updated
    cph_files = list((prob_dir / ".cph").glob("*.prob"))
    assert len(cph_files) > 0
    cph_data = json.loads(cph_files[0].read_text())
    assert len(cph_data["tests"]) == 3


def test_cli_create_async_instant_scaffold(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    spec = {
        "title": "Instant Async Test",
        "category": "dynamic-programming",
        "reference_code": "import sys\nprint(int(sys.stdin.read().strip()) + 1)",
        "test_generator": """
def generate():
    yield ('100\\n', 'stress')
    yield ('200\\n', 'stress')
""",
        "testcases": [
            {"id": 1, "input": "1\n", "output": "2\n", "kind": "sample"}
        ]
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec))

    monkeypatch.setattr(
        "harpy.cli.dispatch_to_cph",
        lambda s, ports=None: {"success": False, "message": "No listener"},
    )

    import sys
    sys.argv = ["harpy", "create", "--async", "-s", str(spec_file)]
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert "Problem Created: instant-async-test" in captured.out
    assert "Background Generator:" in captured.out

    prob_dir = tmp_path / "problems" / "dynamic-programming" / "instant-async-test"
    # Starter code exists immediately
    assert (prob_dir / "instant-async-test.cpp").exists()
    assert (prob_dir / "tests" / "in_01.txt").exists()

    # Wait briefly for background process to finish test generation
    for _ in range(50):
        updated_spec = json.loads((prob_dir / "problem.json").read_text())
        if len(updated_spec["testcases"]) >= 3:
            break
        time.sleep(0.1)

    assert len(updated_spec["testcases"]) == 3
    assert (prob_dir / "tests" / "in_02.txt").exists()
    assert (prob_dir / "tests" / "out_02.txt").read_text().strip() == "101"
    assert (prob_dir / "tests" / "out_03.txt").read_text().strip() == "201"


def test_cli_generate_tests_command(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    prob_dir = tmp_path / "problems" / "sorting-and-searching" / "standalone-test"
    prob_dir.mkdir(parents=True)
    tests_dir = prob_dir / "tests"
    tests_dir.mkdir()

    (tests_dir / "in_01.txt").write_text("7\n")
    (tests_dir / "out_01.txt").write_text("14\n")

    spec = {
        "title": "Standalone Test",
        "slug": "standalone-test",
        "category": "sorting-and-searching",
        "reference_code": "import sys\nprint(int(sys.stdin.read().strip()) * 2)",
        "test_generator": "def generate():\n    yield ('9\\n', 'sample')\n",
        "testcases": [
            {"id": 1, "input": "7\n", "output": "14\n", "kind": "sample"}
        ]
    }
    (prob_dir / "problem.json").write_text(json.dumps(spec, indent=2))
    (prob_dir / "standalone-test.cpp").write_text("// C++ code")

    import sys
    sys.argv = ["harpy", "generate-tests", "standalone-test"]
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert "Successfully generated and verified 1 test cases" in captured.out
    assert (tests_dir / "in_02.txt").read_text().strip() == "9"
    assert (tests_dir / "out_02.txt").read_text().strip() == "18"


def test_cli_generate_tests_piped_stdin(tmp_path: Path, monkeypatch, capsys):
    import io
    monkeypatch.chdir(tmp_path)
    prob_dir = tmp_path / "problems" / "introductory-problems" / "pipe-test"
    prob_dir.mkdir(parents=True)
    tests_dir = prob_dir / "tests"
    tests_dir.mkdir()

    (tests_dir / "in_01.txt").write_text("3\n")
    (tests_dir / "out_01.txt").write_text("30\n")

    spec = {
        "title": "Pipe Test",
        "slug": "pipe-test",
        "category": "introductory-problems",
        "testcases": [
            {"id": 1, "input": "3\n", "output": "30\n", "kind": "sample"}
        ]
    }
    (prob_dir / "problem.json").write_text(json.dumps(spec, indent=2))
    (prob_dir / "pipe-test.cpp").write_text("// C++ code")

    pipe_data = json.dumps({
        "reference_code": "import sys\nprint(int(sys.stdin.read().strip()) * 10)",
        "test_generator": "def generate():\n    yield ('4\\n', 'sample')\n",
    })

    import sys
    monkeypatch.setattr(sys, "stdin", io.StringIO(pipe_data))
    sys.argv = ["harpy", "generate-tests", "pipe-test"]
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert "Successfully generated and verified 1 test cases" in captured.out
    assert (tests_dir / "in_02.txt").read_text().strip() == "4"
    assert (tests_dir / "out_02.txt").read_text().strip() == "40"


