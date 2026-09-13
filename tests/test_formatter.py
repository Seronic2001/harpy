from pathlib import Path
from harpy.formatter import create_problem_workspace
from harpy.models import ProblemSpec, TestCase


def test_single_solution_file_created(tmp_path: Path):
    spec = ProblemSpec(
        title="Single File Test",
        testcases=[TestCase(id=1, input="1\n", output="1\n")],
    )
    ws = create_problem_workspace(spec, base_dir=tmp_path, lang="cpp")

    slug = spec.get_slug()
    prob_dir = tmp_path / slug

    # <slug>.cpp should exist
    assert (prob_dir / f"{slug}.cpp").is_file()
    assert ws["solution"] == prob_dir / f"{slug}.cpp"

    # solution.cpp should NOT exist
    assert not (prob_dir / "solution.cpp").exists()
    assert "compat_solution" not in ws
