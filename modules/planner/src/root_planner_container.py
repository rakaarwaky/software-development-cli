"""Planner composition root — wires three capabilities into AgentPlanner."""

from __future__ import annotations

from shared.src.planner.contract_planner_aggregate import IPlanAggregate

from modules.planner.src.agent_planner_orchestrator import AgentPlanner
from modules.planner.src.capabilities_compute_execution import (
    CapabilitiesComputeExecution,
)
from modules.planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
from modules.planner.src.capabilities_validate_dag import CapabilitiesValidateDag


class PlannerContainer:
    """Construct the planner capabilities and orchestrator (wiring only)."""

    def __init__(self) -> None:
        self._orchestrator = AgentPlanner(
            parser=CapabilitiesParsePrPlan(),
            validator=CapabilitiesValidateDag(),
            computer=CapabilitiesComputeExecution(),
        )

    @property
    def aggregate(self) -> IPlanAggregate:
        return self._orchestrator


def create_planner_feature() -> IPlanAggregate:
    """Fully-wired planner feature aggregate (factory for entry / DI)."""
    return PlannerContainer().aggregate
