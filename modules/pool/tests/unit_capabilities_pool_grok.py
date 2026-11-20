"""Unit tests for AgentPool and CapabilitiesPoolGrok.

Covers:
- FR-POOL-003: unknown agent/action → PoolUsageError (exit_code 2)
- sentinel hit → done (sentinel=true)
- terminal exited with final report → done (final_report=true)
- terminal exited without final report → failed
- single probe, session running → running
- capabilities.poll returns a PoolResult (one public function)
"""

from __future__ import annotations

from typing import Callable

import pytest

from shared.src.common.taxonomy_sdc_error import PoolUsageError
from shared.src.pool.taxonomy_pool_request import PoolRequest

from pool.src.agent_pool_orchestrator import AgentPool
from pool.src.capabilities_pool_grok import CapabilitiesPoolGrok


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture()
def agent() -> AgentPool:
    return AgentPool(grok_cap=CapabilitiesPoolGrok())


# ─── FR-POOL-003: unknown agent/action → PoolUsageError ─────────────


class TestPoolUsageError:
    def test_unknown_agent_raises(self, agent: AgentPool) -> None:
        with pytest.raises(PoolUsageError) as exc:
            agent.execute(PoolRequest(action="poll", agent="hermes", session_id="t1"))
        assert exc.value.exit_code == 2
        assert "unknown agent" in str(exc.value)

    def test_unknown_action_raises(self, agent: AgentPool) -> None:
        with pytest.raises(PoolUsageError) as exc:
            agent.execute(PoolRequest(action="run", agent="grok", session_id="t1"))
        assert exc.value.exit_code == 2
        assert "unknown action" in str(exc.value)


# ─── CapabilitiesPoolGrok.poll with a mock runner ───────────────────


class _Runner:
    """Injectable runner returning canned responses keyed by argv tail."""

    def __init__(self, responses: dict[tuple[str, ...], dict]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, list[str]]] = []

    def __call__(self, orca: str, args: list[str]) -> dict:
        self.calls.append((orca, args))
        return self.responses.get(tuple(args), {})


def _make_cap(responses: dict[tuple[str, ...], dict]) -> CapabilitiesPoolGrok:
    return CapabilitiesPoolGrok(runner=_Runner(responses))


class TestCapabilitiesPollGrok:
    def test_sentinel_hit_returns_done(self) -> None:
        read_res = {
            "result": {
                "terminal": {"status": "running", "tail": ["EXECUTE_PLAN_COMPLETE"]}
            }
        }
        cap = _make_cap({("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res})
        result = cap.poll(PoolRequest(session_id="t1"))
        assert result.status == "done"
        assert result.sentinel is True
        assert result.cycles == 1
        assert result.tail == ["EXECUTE_PLAN_COMPLETE"]

    def test_exited_with_final_report_returns_done(self) -> None:
        read_res = {
            "result": {
                "terminal": {
                    "status": "exited",
                    "tail": ["draft: # PR-42", "─ myomniroute"],
                }
            }
        }
        cap = _make_cap({("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res})
        result = cap.poll(PoolRequest(session_id="t1"))
        assert result.status == "done"
        assert result.final_report is True
        assert result.terminal_status == "exited"

    def test_exited_without_report_returns_failed(self) -> None:
        read_res = {
            "result": {
                "terminal": {
                    "status": "exited",
                    "tail": ["command not found", "─ myomniroute"],
                }
            }
        }
        cap = _make_cap({("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res})
        result = cap.poll(PoolRequest(session_id="t1"))
        assert result.status == "failed"
        assert result.final_report is False
        assert result.terminal_status == "exited"

    def test_running_session_returns_running(self) -> None:
        read_res = {
            "result": {
                "terminal": {"status": "running", "tail": ["grok> ..."]},
            }
        }
        cap = _make_cap({("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res})
        result = cap.poll(PoolRequest(session_id="t1", wait=False))
        assert result.status == "running"
        assert result.sentinel is False
        assert result.cycles == 1

    def test_poll_returns_pool_result(self) -> None:
        read_res = {
            "result": {
                "terminal": {"status": "running", "tail": []},
            }
        }
        cap = _make_cap({("terminal", "read", "--terminal", "t1", "--screen", "--json"): read_res})
        result = cap.poll(PoolRequest(session_id="t1"))
        assert isinstance(result, __import__("shared.src.pool.taxonomy_pool_request", fromlist=["PoolResult"]).PoolResult)
