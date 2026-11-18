"""Acceptance tests for the planner feature.

Proves: business requirement met.
"""

from __future__ import annotations

from pathlib import Path

from planner.src.agent_planner_orchestrator import AgentPlanner
from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
from planner.src.capabilities_validate_dag import CapabilitiesValidateDag
from shared.src.planner.taxonomy_planner_request import PlanRequest


def _valid_design_doc(tmp_path: Path) -> Path:
    doc = tmp_path / "design.md"
    doc.write_text(
        "# Design\n\n"
        "## PR Plan\n\n"
        "### PR 0a: Alpha\n"
        "- Files/components affected: src/a.py\n"
        "- Dependencies: none\n"
        "- Description: Alpha PR\n\n"
        "### PR 1: Beta\n"
        "- Files/components affected: src/b.py\n"
        "- Dependencies: PR 0a\n"
        "- Description: Beta PR\n\n"
        "### PR 2: Gamma\n"
        "- Files/components affected: src/c.py\n"
        "- Dependencies: PR 0a, PR 1\n"
        "- Description: Gamma PR\n",
        encoding="utf-8",
    )
    return doc


def _make_orchestrator() -> AgentPlanner:
    return AgentPlanner(
        parser=CapabilitiesParsePrPlan(),
        validator=CapabilitiesValidateDag(),
        computer=CapabilitiesComputeExecution(),
    )


class TestFRPLAN001Acceptance:
    """FR-PLAN-001: Parse PR Plan — business requirement met."""

    def test_parse_returns_all_three_entries(self, tmp_path: Path) -> None:
        doc = _valid_design_doc(tmp_path)
        result = _make_orchestrator().execute(
            PlanRequest(action="validate", path=str(doc)),
        )
        assert result.pr_count == 3
        assert result.linearized_order == ["pr-0a", "pr-1", "pr-2"]


class TestFRPLAN002Acceptance:
    """FR-PLAN-002: Validate DAG — business requirement met."""

    def test_valid_dag_produces_valid_result(self, tmp_path: Path) -> None:
        doc = _valid_design_doc(tmp_path)
        result = _make_orchestrator().execute(
            PlanRequest(action="validate", path=str(doc)),
        )
        assert result.valid is True


class TestFRPLAN003Acceptance:
    """FR-PLAN-003: Compute Execution Plan — business requirement met."""

    def test_linear_chain_has_expected_levels(self, tmp_path: Path) -> None:
        doc = _valid_design_doc(tmp_path)
        result = _make_orchestrator().execute(
            PlanRequest(action="validate", path=str(doc)),
        )
        assert result.levels == 3
        assert result.max_parallelism == 1
        assert result.level_assignments == {
            "pr-0a": 0,
            "pr-1": 1,
            "pr-2": 2,
        }