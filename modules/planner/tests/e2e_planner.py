"""E2E tests for the planner feature.

Proves: full request lifecycle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from planner.src.agent_planner_orchestrator import AgentPlanner
from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
from planner.src.capabilities_validate_dag import CapabilitiesValidateDag
from shared.src.common.taxonomy_sdc_error import PlanParseError
from shared.src.planner.taxonomy_planner_request import PlanRequest


def _plan_doc(tmp_path: Path) -> Path:
    doc = tmp_path / "plan.md"
    doc.write_text(
        "# Plan Doc\n\n"
        "## PR Plan\n\n"
        "### PR 0a: Alpha\n"
        "- Files/components affected: src/a.py\n"
        "- Dependencies: none\n"
        "- Description: Alpha PR\n\n"
        "### PR 1: Beta\n"
        "- Files/components affected: src/b.py\n"
        "- Dependencies: PR 0a\n"
        "- Description: Beta PR\n",
        encoding="utf-8",
    )
    return doc


def _make_orchestrator() -> AgentPlanner:
    return AgentPlanner(
        parser=CapabilitiesParsePrPlan(),
        validator=CapabilitiesValidateDag(),
        computer=CapabilitiesComputeExecution(),
    )


class TestPlannerE2E:
    """Full lifecycle: read plan document → parse → validate → compute."""

    def test_validate_returns_full_plan_result(self, tmp_path: Path) -> None:
        doc = _plan_doc(tmp_path)
        result = _make_orchestrator().execute(
            PlanRequest(action="validate", path=str(doc)),
        )
        assert result.valid is True
        assert result.pr_count == 2
        assert result.levels == 2
        assert result.max_parallelism == 1

    def test_validate_missing_section_raises_parse_error(self, tmp_path: Path) -> None:
        doc = tmp_path / "bad.md"
        doc.write_text("# No plan here\n", encoding="utf-8")
        with pytest.raises(PlanParseError):
            _make_orchestrator().execute(
                PlanRequest(action="validate", path=str(doc)),
            )