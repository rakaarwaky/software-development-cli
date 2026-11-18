"""Benchmark for planner DAG validation performance."""

from __future__ import annotations

import time

from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
from planner.src.capabilities_validate_dag import CapabilitiesValidateDag
from shared.src.planner.taxonomy_planner_request import PrEntryList


def _large_design_doc(num_prs: int) -> str:
    """Generate a PR Plan section with N chained PRs."""
    lines = ["# Design", "", "## PR Plan", ""]
    for i in range(num_prs):
        deps = f"PR {i - 1}" if i > 0 else "none"
        lines.extend(
            [
                f"### PR {i}: Task {i}",
                "- Files/components affected: src/f.py",
                f"- Dependencies: {deps}",
                "- Description: Task description",
                "",
            ]
        )
    return "\n".join(lines)


def bench_parse_plan() -> None:
    """Benchmark parse_plan with 100 PR entries."""
    doc = _large_design_doc(100)
    parser = CapabilitiesParsePrPlan()
    start = time.perf_counter()
    parser.parse_plan(PrEntryList(text=doc))
    elapsed = time.perf_counter() - start
    print(f"parse_plan(100 PRs): {elapsed * 1000:.2f}ms")


def bench_validate_dag() -> None:
    """Benchmark validate_dag with 100 chained entries."""
    entries = PrEntryList(
        text=_large_design_doc(100),
    )
    parser = CapabilitiesParsePrPlan()
    parse_result = parser.parse_plan(entries)
    validator = CapabilitiesValidateDag()
    start = time.perf_counter()
    validator.validate_dag(
        PrEntryList(entries=parse_result.entries),
    )
    elapsed = time.perf_counter() - start
    print(f"validate_dag(100 PRs): {elapsed * 1000:.2f}ms")


def bench_compute_execution() -> None:
    """Benchmark compute_levels with 100 chained entries."""
    entries = PrEntryList(
        text=_large_design_doc(100),
    )
    parser = CapabilitiesParsePrPlan()
    parse_result = parser.parse_plan(entries)
    computer = CapabilitiesComputeExecution()
    start = time.perf_counter()
    computer.compute_levels(
        PrEntryList(entries=parse_result.entries),
    )
    elapsed = time.perf_counter() - start
    print(f"compute_levels(100 PRs): {elapsed * 1000:.2f}ms")


if __name__ == "__main__":
    bench_parse_plan()
    bench_validate_dag()
    bench_compute_execution()