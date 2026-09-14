from harpy.models import ProblemSpec, TestCase, TestCaseKind


def test_problem_spec_markdown():
    spec = ProblemSpec(
        title="Two Sum",
        difficulty="Easy",
        tags=["Array", "Hash Table"],
        description="Given an array of integers, return indices of two numbers such that they add up to target.",
        input_format="First line contains N and target. Second line contains N integers.",
        output_format="Output two space-separated indices.",
        constraints=["$2 \\le N \\le 10^4$", "$-10^9 \\le A_i \\le 10^9$"],
        testcases=[
            TestCase(
                id=1,
                input="4 9\n2 7 11 15\n",
                output="0 1\n",
                kind=TestCaseKind.SAMPLE,
                explanation="2 + 7 = 9, so indices are 0 and 1.",
            )
        ],
    )

    md = spec.to_markdown()
    assert "# Two Sum" in md
    assert "**Difficulty**: `Easy`" in md
    assert "## Constraints" in md
    assert "2 + 7 = 9" in md


def test_competitive_companion_dict():
    spec = ProblemSpec(
        title="Two Sum",
        testcases=[
            TestCase(
                id=1,
                input="4 9\n2 7 11 15\n",
                output="0 1\n",
            )
        ],
    )

    cc = spec.to_competitive_companion_dict()
    assert cc["name"] == "Two Sum"
    assert cc["group"] == "Harpy"
    assert len(cc["tests"]) == 1
    assert cc["tests"][0]["input"] == "4 9\n2 7 11 15\n"
    assert cc["tests"][0]["output"] == "0 1\n"


def test_testcase_optional_output():
    # Verify TestCase can be instantiated without output (for oracle generation)
    tc = TestCase(input="10 20\n")
    assert tc.output == ""
    assert tc.normalized_output() == ""
    assert tc.kind == TestCaseKind.SAMPLE

