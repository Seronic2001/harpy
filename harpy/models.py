from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TestCaseKind(str, Enum):
    __test__ = False
    SAMPLE = "sample"
    EDGE = "edge"
    STRESS = "stress"
    CUSTOM = "custom"


class TestCase(BaseModel):
    __test__ = False
    id: int | str = 0
    input: str
    output: str
    kind: TestCaseKind = TestCaseKind.SAMPLE
    explanation: Optional[str] = None

    def normalized_input(self) -> str:
        # Ensures input ends with a newline if non-empty
        val = self.input.replace("\r\n", "\n")
        if val and not val.endswith("\n"):
            val += "\n"
        return val

    def normalized_output(self) -> str:
        val = self.output.replace("\r\n", "\n").rstrip()
        return val


class ProblemSpec(BaseModel):
    title: str
    slug: Optional[str] = None
    difficulty: str = "Medium"
    tags: List[str] = Field(default_factory=list)
    description: str = ""
    input_format: str = ""
    output_format: str = ""
    constraints: List[str] = Field(default_factory=list)
    time_limit_ms: int = 1000
    memory_limit_mb: int = 256
    testcases: List[TestCase] = Field(default_factory=list)
    reference_code: Optional[str] = None
    cpp_signature: Optional[str] = None
    cpp_main_parser: Optional[str] = None
    starter_templates: Dict[str, str] = Field(default_factory=dict)

    def get_slug(self) -> str:
        if self.slug:
            return self.slug
        clean = re.sub(r"[^\w\s-]", "", self.title.lower())
        return re.sub(r"[-\s]+", "-", clean).strip("-") or "problem"

    def to_competitive_companion_dict(self) -> Dict[str, Any]:
        """Convert to the standard Competitive Companion JSON format."""
        return {
            "name": self.title,
            "group": "Harpy",
            "url": "",
            "interactive": False,
            "memoryLimit": self.memory_limit_mb,
            "timeLimit": self.time_limit_ms,
            "tests": [
                {
                    "input": tc.normalized_input(),
                    "output": (tc.normalized_output() + "\n") if tc.output else "",
                }
                for tc in self.testcases
            ],
            "testType": "single",
            "input": {"type": "stdin"},
            "output": {"type": "stdout"},
            "languages": {
                "java": {
                    "mainClass": "Main",
                    "taskClass": "".join(
                        part.capitalize()
                        for part in re.split(r"[\s_-]+", self.get_slug())
                    ),
                }
            },
        }

    def to_markdown(self) -> str:
        """Render standard LeetCode / competitive programming style markdown."""
        lines = [
            f"# {self.title}",
            "",
            f"**Difficulty**: `{self.difficulty}`",
        ]
        if self.tags:
            lines.append(f"**Topics**: {', '.join(f'`{t}`' for t in self.tags)}")
        lines.extend(
            [
                f"**Time Limit**: `{self.time_limit_ms} ms` | **Memory Limit**: `{self.memory_limit_mb} MB`",
                "",
                "---",
                "",
                "## Problem Description",
                "",
                self.description.strip(),
                "",
            ]
        )

        if self.input_format:
            lines.extend(
                [
                    "## Input Format",
                    "",
                    self.input_format.strip(),
                    "",
                ]
            )

        if self.output_format:
            lines.extend(
                [
                    "## Output Format",
                    "",
                    self.output_format.strip(),
                    "",
                ]
            )

        if self.constraints:
            lines.extend(
                [
                    "## Constraints",
                    "",
                ]
            )
            for c in self.constraints:
                lines.append(f"- {c}")
            lines.append("")

        if self.testcases:
            lines.extend(
                [
                    "---",
                    "",
                    "## Examples",
                    "",
                ]
            )
            sample_idx = 1
            for tc in self.testcases:
                if tc.kind == TestCaseKind.SAMPLE or not any(
                    t.kind == TestCaseKind.SAMPLE for t in self.testcases
                ):
                    lines.extend(
                        [
                            f"### Example {sample_idx}",
                            "",
                            "**Input:**",
                            "```text",
                            tc.input.strip(),
                            "```",
                            "",
                            "**Output:**",
                            "```text",
                            tc.output.strip(),
                            "```",
                            "",
                        ]
                    )
                    if tc.explanation:
                        lines.extend(
                            [
                                f"**Explanation:** {tc.explanation}",
                                "",
                            ]
                        )
                    sample_idx += 1

        return "\n".join(lines).strip() + "\n"
