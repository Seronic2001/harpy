from pathlib import Path
from harpy.models import TestCase
from harpy.runner import SolutionRunner, compare_outputs


def test_compare_outputs():
    assert compare_outputs("hello \n", "hello\n\n") is True
    assert compare_outputs("1.0000001", "1.0000002", float_epsilon=1e-5) is True
    assert compare_outputs("1 2 3", "1   2\n3") is True
    assert compare_outputs("1 2", "1 3") is False


def test_python_solution_runner(tmp_path: Path):
    sol_file = tmp_path / "solution.py"
    sol_file.write_text(
        """
import sys
a, b = map(int, sys.stdin.read().split())
print(a + b)
""",
        encoding="utf-8",
    )

    runner = SolutionRunner(sol_file)
    ok, err = runner.compile()
    assert ok is True

    # 1. Passing case
    res1 = runner.run_case(TestCase(id=1, input="3 4\n", output="7\n"))
    assert res1.status == "PASS"

    # 2. Failing case
    res2 = runner.run_case(TestCase(id=2, input="3 4\n", output="8\n"))
    assert res2.status == "FAIL"

    runner.cleanup()


def test_cpp_solution_runner(tmp_path: Path):
    sol_file = tmp_path / "solution.cpp"
    sol_file.write_text(
        """
#include <iostream>
using namespace std;
int main() {
    long long a, b;
    if (cin >> a >> b) {
        cout << a * b << endl;
    }
    return 0;
}
""",
        encoding="utf-8",
    )

    runner = SolutionRunner(sol_file)
    ok, err = runner.compile()
    assert ok is True, f"C++ Compilation failed: {err}"

    res = runner.run_case(TestCase(id=1, input="6 7\n", output="42\n"))
    assert res.status == "PASS"

    runner.cleanup()
