"""E2E tests for the pool feature.

Proves: full request lifecycle through the agent orchestrator.
"""

from __future__ import annotations

from typing import Callable

from shared.src.pool.taxonomy_pool_request import PoolRequest

from pool.src.agent_pool_orchestrator import AgentPool
from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], dict]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, list[str]]] = []

    def __call__(self, orca: str, args: list[str]) -> dict:
        self.calls.append((orca, args))
        return self.responses.get(tuple(args), {})


class TestPoolE2E:
    """Full lifecycle: probe → done / running via AgentPool.execute."""

    def _make_agent(self, responses: dict[tuple[str, ...], dict]) -> AgentPool:
        return AgentPool(grok_cap=CapabilitiesPoolGrok(runner=_FakeRunner(responses)))

    def test_single_probe_done_via_agent(self) -> None:
        read_res = {
            "result": {
                "terminal": {"status": "running", "tail": ["EXECUTE_PLAN_COMPLETE"]}
            }
        }
        agent = self._make_agent(
            {("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res}
        )
        result = agent.execute(PoolRequest(session_id="t1", wait=False))
        assert result.status == "done"
        assert result.sentinel is True

    def test_single_probe_running_via_agent(self) -> None:
        read_res = {
            "result": {"terminal": {"status": "running", "tail": ["grok> ..."]}}
        }
        agent = self._make_agent(
            {("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res}
        )
        result = agent.execute(PoolRequest(session_id="t1", wait=False))
        assert result.status == "running"
        assert result.sentinel is False

    def test_failed_on_exit_without_report_via_agent(self) -> None:
        read_res = {
            "result": {
                "terminal": {
                    "status": "exited",
                    "tail": ["error: command not found", "─ myomniroute"],
                }
            }
        }
        agent = self._make_agent(
            {("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res}
        )
        result = agent.execute(PoolRequest(session_id="t1", wait=False))
        assert result.status == "failed"
        assert result.final_report is False
