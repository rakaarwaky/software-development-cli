"""Root container tests for the planner feature (AES test layer)."""

import sys
import unittest
from pathlib import Path

_MODULES_ROOT = Path(__file__).resolve().parents[3]
for _m in ("shared", "cli", "planner", "memory", "host"):
    _src = _MODULES_ROOT / "modules" / _m / "src"
    if _src.is_dir() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
if str(_MODULES_ROOT / "modules") not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT / "modules"))

from parameterized import parameterized

from modules.planner.src.agent_planner_orchestrator import AgentPlanner
from modules.planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
from modules.planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
from modules.planner.src.capabilities_validate_dag import CapabilitiesValidateDag
from modules.planner.src.root_planner_container import PlannerContainer, create_planner_feature
from shared.src.planner.contract_planner_aggregate import IPlanAggregate
from shared.src.planner.contract_planner_protocol import (
    IPlanComputeProtocol,
    IPlanParseProtocol,
    IPlanValidateProtocol,
)


class TestPlannerContainer(unittest.TestCase):
    """Test the planner composition root wiring."""

    def setUp(self) -> None:
        self.container = PlannerContainer()

    def test_container_implements_aggregate_contract(self) -> None:
        self.assertIsInstance(self.container.aggregate, IPlanAggregate)

    def test_factory_returns_aggregate(self) -> None:
        self.assertIsInstance(create_planner_feature(), IPlanAggregate)

    def test_factory_wires_same_classes(self) -> None:
        feature = create_planner_feature()
        self.assertIsInstance(feature, AgentPlanner)
        self.assertIsInstance(feature._parser, CapabilitiesParsePrPlan)
        self.assertIsInstance(feature._validator, CapabilitiesValidateDag)
        self.assertIsInstance(feature._computer, CapabilitiesComputeExecution)

    def test_wires_all_protocols(self) -> None:
        feature = self.container.aggregate
        self.assertIsInstance(feature, AgentPlanner)
        self.assertIsInstance(feature._parser, IPlanParseProtocol)
        self.assertIsInstance(feature._validator, IPlanValidateProtocol)
        self.assertIsInstance(feature._computer, IPlanComputeProtocol)

    @parameterized.expand([
        ("first", "validate", "nonexistent.md", 0),
        ("second", "validate", "nonexistent.md", 0),
    ])
    def test_container_dispatch_returns_int(
        self, _case: str, action: str, path: str, expected_rc: int,
    ) -> None:
        from shared.src.planner.taxonomy_planner_request import PlanRequest
        result = self.container.aggregate.execute(
            PlanRequest(action=action, path=path),
        )
        self.assertIsInstance(result, PlanResult)


if __name__ == "__main__":
    unittest.main()