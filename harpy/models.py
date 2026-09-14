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
    output: str = ""
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


CSES_CATEGORIES: Dict[str, List[str]] = {
    "dynamic-programming": ["dp", "dynamic-programming", "dynamic programming", "memoization", "knapsack", "lis", "grid-dp", "digit-dp", "interval-dp"],
    "graph-algorithms": ["graph", "graphs", "graph-algorithms", "graph algorithms", "bfs", "dfs", "dijkstra", "bellman-ford", "floyd-warshall", "mst", "topological-sort", "topological sort", "shortest-path", "shortest path"],
    "tree-algorithms": ["tree", "trees", "tree-algorithms", "tree algorithms", "binary-tree", "binary tree", "bst", "lca", "tree-dp"],
    "sorting-and-searching": ["sorting", "searching", "sorting-and-searching", "sorting and searching", "binary-search", "binary search", "two-pointers", "two pointers", "sliding-window", "sliding window", "ternary-search"],
    "greedy-algorithms": ["greedy", "greedy-algorithms", "greedy algorithms", "interval-scheduling"],
    "range-queries": ["range-queries", "range queries", "segment-tree", "segment tree", "fenwick", "fenwick-tree", "bit", "sparse-table"],
    "mathematics": ["math", "mathematics", "maths", "number-theory", "number theory", "combinatorics", "modular-arithmetic", "probability"],
    "string-algorithms": ["string", "strings", "string-algorithms", "string algorithms", "trie", "kmp", "z-algorithm", "suffix-array", "hashing"],
    "geometry": ["geometry", "convex-hull", "polygon", "point-location"],
    "bit-manipulation": ["bit", "bits", "bit-manipulation", "bit manipulation", "bitmask"],
    "introductory-problems": ["intro", "introductory", "introductory-problems", "introductory problems", "simulation", "implementation", "ad-hoc", "basics"],
    "advanced-techniques": ["advanced", "advanced-techniques", "advanced techniques", "meet-in-the-middle", "mo", "hld"],
}

DEFAULT_CATEGORY = "general"


def normalize_category(category: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """Normalize a category string or infer one from tags to a canonical CSES category."""
    # 1. Check explicit category
    if category:
        c_clean = category.strip().lower().replace("_", "-")
        for canon, aliases in CSES_CATEGORIES.items():
            if c_clean == canon or c_clean in aliases:
                return canon
        clean_custom = re.sub(r"[^\w\s-]", "", c_clean)
        return re.sub(r"[-\s]+", "-", clean_custom).strip("-") or DEFAULT_CATEGORY

    # 2. Infer from tags
    if tags:
        for tag in tags:
            t_clean = tag.strip().lower().replace("_", "-")
            # Exact match check first
            for canon, aliases in CSES_CATEGORIES.items():
                if t_clean == canon or t_clean in aliases:
                    return canon
            # Token/word boundary match to prevent short alias false positives (e.g. 'mo' in 'memoization')
            for canon, aliases in CSES_CATEGORIES.items():
                for alias in aliases:
                    pattern = r"(^|[\s_-])" + re.escape(alias) + r"($|[\s_-])"
                    if re.search(pattern, t_clean):
                        return canon

    return DEFAULT_CATEGORY


class ProblemSpec(BaseModel):
    title: str
    slug: Optional[str] = None
    category: Optional[str] = None
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

    def get_category(self) -> str:
        return normalize_category(self.category, self.tags)

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
            f"**Difficulty**: `{self.difficulty}` | **Category**: `{self.get_category()}`",
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
