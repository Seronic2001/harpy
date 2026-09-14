from pathlib import Path
import json
from harpy.models import (
    CSES_CATEGORIES,
    ProblemSpec,
    TestCase,
    normalize_category,
)
from harpy.formatter import create_problem_workspace
from harpy.cli import find_solution_file


def test_normalize_category_canonical():
    assert normalize_category("dynamic-programming") == "dynamic-programming"
    assert normalize_category("graph-algorithms") == "graph-algorithms"
    assert normalize_category("tree-algorithms") == "tree-algorithms"
    assert normalize_category("sorting-and-searching") == "sorting-and-searching"
    assert normalize_category("greedy-algorithms") == "greedy-algorithms"
    assert normalize_category("range-queries") == "range-queries"
    assert normalize_category("mathematics") == "mathematics"
    assert normalize_category("string-algorithms") == "string-algorithms"
    assert normalize_category("geometry") == "geometry"
    assert normalize_category("bit-manipulation") == "bit-manipulation"
    assert normalize_category("introductory-problems") == "introductory-problems"
    assert normalize_category("advanced-techniques") == "advanced-techniques"


def test_normalize_category_aliases():
    assert normalize_category("dp") == "dynamic-programming"
    assert normalize_category("DP") == "dynamic-programming"
    assert normalize_category("Dynamic Programming") == "dynamic-programming"
    assert normalize_category("graphs") == "graph-algorithms"
    assert normalize_category("tree") == "tree-algorithms"
    assert normalize_category("trees") == "tree-algorithms"
    assert normalize_category("sorting") == "sorting-and-searching"
    assert normalize_category("binary search") == "sorting-and-searching"
    assert normalize_category("greedy") == "greedy-algorithms"
    assert normalize_category("segment tree") == "range-queries"
    assert normalize_category("math") == "mathematics"
    assert normalize_category("strings") == "string-algorithms"
    assert normalize_category("geometry") == "geometry"
    assert normalize_category("bitmask") == "bit-manipulation"
    assert normalize_category("intro") == "introductory-problems"


def test_normalize_category_inference_from_tags():
    # If category is None, infer from tags
    assert normalize_category(None, tags=["Shortest Paths", "Dijkstra"]) == "graph-algorithms"
    assert normalize_category(None, tags=["Memoization", "Knapsack"]) == "dynamic-programming"
    assert normalize_category(None, tags=["Binary Search", "Two Pointers"]) == "sorting-and-searching"
    assert normalize_category(None, tags=["Number Theory"]) == "mathematics"
    # Fallback to general if no tags or unrecognized
    assert normalize_category(None, tags=["UnknownTag"]) == "general"
    assert normalize_category(None, tags=[]) == "general"


def test_problem_spec_category_and_markdown():
    spec = ProblemSpec(
        title="Coin Combinations I",
        category="dp",
        tags=["Dynamic Programming"],
        testcases=[TestCase(id=1, input="3 9\n2 3 5\n", output="8\n")],
    )
    assert spec.get_category() == "dynamic-programming"
    md = spec.to_markdown()
    assert "| **Category**: `dynamic-programming`" in md


def test_workspace_scaffolding_with_category(tmp_path: Path):
    spec = ProblemSpec(
        title="Flight Routes Check",
        category="graph-algorithms",
        testcases=[TestCase(id=1, input="4 5\n1 2\n2 3\n3 1\n1 4\n4 1\n", output="YES\n")],
    )
    ws = create_problem_workspace(spec, base_dir=tmp_path, lang="cpp")

    category = "graph-algorithms"
    slug = "flight-routes-check"
    expected_dir = tmp_path / category / slug

    assert ws["category"] == category
    assert ws["dir"] == expected_dir
    assert (expected_dir / f"{slug}.cpp").is_file()
    assert (expected_dir / "problem.md").is_file()
    assert (expected_dir / "problem.json").is_file()
    assert (expected_dir / "tests" / "in_01.txt").is_file()
    assert (expected_dir / "tests" / "out_01.txt").is_file()


def test_cli_find_solution_file_in_category_folder(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Create category layout
    prob_dir = tmp_path / "problems" / "dynamic-programming" / "coin-combinations-i"
    prob_dir.mkdir(parents=True)
    sol_file = prob_dir / "coin-combinations-i.cpp"
    sol_file.write_text("// solution")

    # 1. By slug
    res = find_solution_file("coin-combinations-i")
    assert res is not None
    assert res.resolve() == sol_file.resolve()

    # 2. By file name
    res2 = find_solution_file("coin-combinations-i.cpp")
    assert res2 is not None
    assert res2.resolve() == sol_file.resolve()

    # 3. By relative path
    res3 = find_solution_file("problems/dynamic-programming/coin-combinations-i/coin-combinations-i.cpp")
    assert res3 is not None
    assert res3.resolve() == sol_file.resolve()


def test_cli_find_solution_file_legacy_fallback(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Legacy flat structure: problems/<slug>/<slug>.cpp
    prob_dir = tmp_path / "problems" / "legacy-problem"
    prob_dir.mkdir(parents=True)
    sol_file = prob_dir / "legacy-problem.cpp"
    sol_file.write_text("// legacy")

    res = find_solution_file("legacy-problem")
    assert res is not None
    assert res.resolve() == sol_file.resolve()


def test_cmd_push_finds_nested_problem(tmp_path: Path, monkeypatch, capsys):
    from harpy.cli import cmd_push
    import argparse

    monkeypatch.chdir(tmp_path)
    prob_dir = tmp_path / "problems" / "dynamic-programming" / "nested-problem"
    prob_dir.mkdir(parents=True)
    spec = ProblemSpec(title="Nested Problem", category="dynamic-programming")
    (prob_dir / "problem.json").write_text(spec.model_dump_json(), encoding="utf-8")

    monkeypatch.setattr("harpy.cli.dispatch_to_cph", lambda s, ports=None: {"success": True, "message": "Dispatched to CPH"})

    args = argparse.Namespace(target="nested-problem", port=None)
    code = cmd_push(args)
    assert code == 0
    captured = capsys.readouterr()
    assert "Dispatched to CPH" in captured.out

