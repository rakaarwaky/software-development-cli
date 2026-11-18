"""Integration tests for planner module and DI wiring.

Proves: module / crate / package + DI wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cli.src.surface_sdc_command import reset_capabilities, set_capabilities
from planner.src.agent_planner_orchestrator import AgentPlanner
from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
from planner.src.capabilities_validate_dag import CapabilitiesValidateDag
from shared.src.planner.contract_planner_aggregate import IPlanAggregate


class TestPlannerDIWiring:
    """Planner capabilities wired through root container and surface."""

    def test_root_container_wires_all_capabilities(self) -> None:
        from planner.src.root_planner_container import PlannerContainer

        container = PlannerContainer()
        assert isinstance(container.aggregate, IPlanAggregate)

    def test_set_capabilities_accepts_planner_aggregate(self) -> None:
        reset_capabilities()
        planner = AgentPlanner(
            parser=CapabilitiesParsePrPlan(),
            validator=CapabilitiesValidateDag(),
            computer=CapabilitiesComputeExecution(),
        )
        set_capabilities(
            host=MagicMock(),
            memory=MagicMock(),
            planner=planner,
        )

    def test_root_container_create_planner_feature_is_callable(self) -> None:
        from planner.src.root_planner_container import create_planner_feature

        feature = create_planner_feature()
        assert callable(getattr(feature, "execute", None))