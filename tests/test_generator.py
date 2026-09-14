import json
from pathlib import Path
import pytest
from harpy.models import TestCaseKind
from harpy.oracle import (
    execute_test_generator,
    GeneratorExecutionError,
)
from harpy.cli import main


def test_execute_test_generator_yield_strings():
    code = """
def generate():
    yield "10 20\\n"
    yield "30 40\\n"
"""
    cases = execute_test_generator(code)
    assert len(cases) == 2
    assert cases[0] == ("10 20\n", TestCaseKind.SAMPLE, None)
    assert cases[1] == ("30 40\n", TestCaseKind.SAMPLE, None)


def test_execute_test_generator_yield_tuples():
    code = """
def generate():
    yield ("1 2\\n", "sample", "First sample")
    yield ("0 0\\n", "edge", "Corner case")
    yield ("1000 2000\\n", "stress", None)
"""
    cases = execute_test_generator(code)
    assert len(cases) == 3
    assert cases[0] == ("1 2\n", TestCaseKind.SAMPLE, "First sample")
    assert cases[1] == ("0 0\n", TestCaseKind.EDGE, "Corner case")
    assert cases[2] == ("1000 2000\n", TestCaseKind.STRESS, None)


def test_execute_test_generator_yield_dicts():
    code = """
def generate_inputs():
    return [
        {"input": "5 5\\n", "kind": "sample"},
        {"input": "99 99\\n", "kind": "stress", "explanation": "Max bounds"}
    ]
"""
    cases = execute_test_generator(code)
    assert len(cases) == 2
    assert cases[0] == ("5 5\n", TestCaseKind.SAMPLE, None)
    assert cases[1] == ("99 99\n", TestCaseKind.STRESS, "Max bounds")


def test_execute_test_generator_error_handling():
    code = """
def generate():
    raise ValueError("Intentional generator failure")
"""
    with pytest.raises(GeneratorExecutionError) as exc_info:
        execute_test_generator(code)
    assert "ValueError: Intentional generator failure" in str(exc_info.value)


def test_cli_create_with_test_generator(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    spec = {
        "title": "Algorithmic Generator Test",
        "category": "tree-algorithms",
        "reference_code": "import sys\nprint(int(sys.stdin.read().strip()) * 3)",
        "test_generator": """
def generate():
    for i in range(1, 4):
        yield (f"{i}\\n", "sample")
""",
    }
    spec_file = tmp_path / "spec.json"
    spec_file.write_text(json.dumps(spec), encoding="utf-8")

    monkeypatch.setattr(
        "harpy.cli.dispatch_to_cph",
        lambda s, ports=None: {"success": False, "message": "No listener"},
    )

    import sys
    sys.argv = ["harpy", "create", "-s", str(spec_file)]
    code = main()
    assert code == 0

    captured = capsys.readouterr()
    assert "Generated 3 test cases programmatically" in captured.out
    assert "Verified 3 total test cases with reference oracle" in captured.out

    prob_dir = tmp_path / "problems" / "tree-algorithms" / "algorithmic-generator-test"
    assert (prob_dir / "tests" / "out_01.txt").read_text().strip() == "3"
    assert (prob_dir / "tests" / "out_02.txt").read_text().strip() == "6"
    assert (prob_dir / "tests" / "out_03.txt").read_text().strip() == "9"
