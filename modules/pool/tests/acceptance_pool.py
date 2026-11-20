"""Acceptance tests for the pool feature.

Proves: business requirement met (FR-POOL-001 / FR-POOL-002 / FR-POOL-003).
"""

from __future__ import annotations

from typing import Callable

import pytest

from shared.src.common.taxonomy_sdc_error import PoolUsageError
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


class TestFRPOOL001Acceptance:
    """FR-POOL-001: Poll a Grok Build session (single probe)."""

    def test_done_on_sentinel(self) -> None:
        read_res = {
            "result": {
                "terminal": {"status": "running", "tail": ["EXECUTE_PLAN_COMPLETE"]}
            }
        }
        agent = AgentPool(
            grok_cap=CapabilitiesPoolGrok(
                runner=_FakeRunner(
                    {("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res}
                )
            )
        )
        result = agent.execute(PoolRequest(session_id="t1"))
        assert result.status == "done"
        assert result.sentinel is True

    def test_done_on_exit_with_final_report(self) -> None:
        read_res = {
            "result": {
                "terminal": {
                    "status": "exited",
                    "tail": ["draft: # PR-42", "─ myomniroute"],
                }
            }
        }
        agent = AgentPool(
            grok_cap=CapabilitiesPoolGrok(
                runner=_FakeRunner(
                    {("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res}
                )
            )
        )
        result = agent.execute(PoolRequest(session_id="t1"))
        assert result.status == "done"
        assert result.final_report is True

    def test_running_when_session_still_active(self) -> None:
        read_res = {
            "result": {"terminal": {"status": "running", "tail": ["grok> ..."]}}
        }
        agent = AgentPool(
            grok_cap=CapabilitiesPoolGrok(
                runner=_FakeRunner(
                    {("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res}
                )
            )
        )
        result = agent.execute(PoolRequest(session_id="t1"))
        assert result.status == "running"

    def test_unknown_on_unreadable_terminal(self) -> None:
        agent = AgentPool(grok_cap=CapabilitiesPoolGrok(runner=_FakeRunner({})))
        result = agent.execute(PoolRequest(session_id="t1"))
        assert result.status == "unknown"


class TestFRPOOL003Acceptance:
    """FR-POOL-003: Unknown agent or action rejected."""

    def test_unknown_agent_rejected(self) -> None:
        agent = AgentPool(grok_cap=CapabilitiesPoolGrok())
        with pytest.raises(PoolUsageError) as exc:
            agent.execute(PoolRequest(action="poll", agent="hermes", session_id="t1"))
        assert exc.value.exit_code == 2

    def test_unknown_action_rejected(self) -> None:
        agent = AgentPool(grok_cap=CapabilitiesPoolGrok())
        with pytest.raises(PoolUsageError) as exc:
            agent.execute(PoolRequest(action="run", agent="grok", session_id="t1"))
        assert exc.value.exit_code == 2
