"""Contract tests for planner protocols.

Verifies that planner capabilities implement their protocol interfaces:
- IPlanParseProtocol
- IPlanValidateProtocol
- IPlanComputeProtocol
- IPlanAggregate
"""

from __future__ import annotations

from shared.src.planner.contract_planner_aggregate import IPlanAggregate
from shared.src.planner.contract_planner_protocol import (
    IPlanComputeProtocol,
    IPlanParseProtocol,
    IPlanValidateProtocol,
)


class TestIPlanParseProtocol:
    """IPlanParseProtocol contract: parse_plan method exists."""

    def test_capabilities_parse_pr_plan_implements_protocol(self) -> None:
        from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan

        parser = CapabilitiesParsePrPlan()
        assert isinstance(parser, IPlanParseProtocol)

    def test_capabilities_parse_pr_plan_has_parse_plan_method(self) -> None:
        from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan

        parser = CapabilitiesParsePrPlan()
        assert hasattr(parser, "parse_plan")
        assert callable(parser.parse_plan)


class TestIPlanValidateProtocol:
    """IPlanValidateProtocol contract: validate_dag method exists."""

    def test_capabilities_validate_dag_implements_protocol(self) -> None:
        from planner.src.capabilities_validate_dag import CapabilitiesValidateDag

        validator = CapabilitiesValidateDag()
        assert isinstance(validator, IPlanValidateProtocol)

    def test_capabilities_validate_dag_has_validate_dag_method(self) -> None:
        from planner.src.capabilities_validate_dag import CapabilitiesValidateDag

        validator = CapabilitiesValidateDag()
        assert hasattr(validator, "validate_dag")
        assert callable(validator.validate_dag)


class TestIPlanComputeProtocol:
    """IPlanComputeProtocol contract: compute_levels method exists."""

    def test_capabilities_compute_execution_implements_protocol(self) -> None:
        from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution

        computer = CapabilitiesComputeExecution()
        assert isinstance(computer, IPlanComputeProtocol)

    def test_capabilities_compute_execution_has_compute_levels_method(self) -> None:
        from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution

        computer = CapabilitiesComputeExecution()
        assert hasattr(computer, "compute_levels")
        assert callable(computer.compute_levels)


class TestIPlanAggregate:
    """IPlanAggregate contract: execute method exists."""

    def test_agent_planner_implements_aggregate(self) -> None:
        from planner.src.agent_planner_orchestrator import AgentPlanner
        from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
        from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
        from planner.src.capabilities_validate_dag import CapabilitiesValidateDag

        orchestrator = AgentPlanner(
            parser=CapabilitiesParsePrPlan(),
            validator=CapabilitiesValidateDag(),
            computer=CapabilitiesComputeExecution(),
        )
        assert isinstance(orchestrator, IPlanAggregate)

    def test_agent_planner_has_execute_method(self) -> None:
        from planner.src.agent_planner_orchestrator import AgentPlanner
        from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
        from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
        from planner.src.capabilities_validate_dag import CapabilitiesValidateDag

        orchestrator = AgentPlanner(
            parser=CapabilitiesParsePrPlan(),
            validator=CapabilitiesValidateDag(),
            computer=CapabilitiesComputeExecution(),
        )
        assert hasattr(orchestrator, "execute")
        assert callable(orchestrator.execute)


class TestRootContainerContract:
    """Root container exposes IPlanAggregate."""

    def test_create_planner_feature_returns_aggregate(self) -> None:
        from planner.src.root_planner_container import create_planner_feature

        feature = create_planner_feature()
        assert isinstance(feature, IPlanAggregate)