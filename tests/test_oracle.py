import pytest
from harpy.models import TestCaseKind
from harpy.oracle import (
    OracleTimeoutError,
    run_reference_solution,
    verify_and_generate_testcases,
)


def test_oracle_execution():
    ref_code = """
import sys
def solve():
    data = sys.stdin.read().split()
    if not data: return
    n = int(data[0])
    target = int(data[1])
    nums = [int(x) for x in data[2:]]
    seen = {}
    for i, x in enumerate(nums):
        diff = target - x
        if diff in seen:
            print(f"{seen[diff]} {i}")
            return
        seen[x] = i

if __name__ == "__main__":
    solve()
"""
    raw_input = "4 9\n2 7 11 15\n"
    out = run_reference_solution(ref_code, raw_input)
    assert out.strip() == "0 1"


def test_verify_and_generate_testcases():
    ref_code = """
import sys
x = sys.stdin.read().strip()
print(f"HELLO {x}")
"""
    inputs = [
        ("Alice", TestCaseKind.SAMPLE, "Greeting Alice"),
        ("Bob", TestCaseKind.EDGE, "Greeting Bob"),
    ]
    cases = verify_and_generate_testcases(ref_code, inputs)
    assert len(cases) == 2
    assert cases[0].output.strip() == "HELLO Alice"
    assert cases[1].output.strip() == "HELLO Bob"
    assert cases[0].kind == TestCaseKind.SAMPLE
    assert cases[1].kind == TestCaseKind.EDGE


def test_oracle_timeout():
    ref_code = """
import time
time.sleep(5)
"""
    with pytest.raises(OracleTimeoutError):
        run_reference_solution(ref_code, "test", timeout_sec=0.5)
