"""Tests for HostAgent (agent_host_orchestrator).

Covers:
- dispatch setup / cleanup routes correctly
- Unknown action → HostError (not ValueError)
- request.paths None vs empty list guard
- Constructor injection via HostAgent.create()
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.common.taxonomy_sdc_vo import SkillSubdir
from shared.src.host.contract_host_protocol import (
    IHostCleanupProtocol,
    IHostSetupProtocol,
)
from shared.src.host.taxonomy_host_request import HostRequest, HostResult

from host.src.agent_host_orchestrator import HostAgent


# ─── Fake capabilities ───────────────────────────────────────────────


class FakeSetup:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def setup(self, subdir: SkillSubdir) -> HostResult:
        self.calls.append(subdir)
        return HostResult(scratch_dir=f"/tmp/{subdir}")


class FakeCleanup:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def cleanup(self, paths: list[str]) -> HostResult:
        self.calls.append(list(paths))
        return HostResult(failed_count=0)


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture()
def setup_cap():
    return FakeSetup()


@pytest.fixture()
def cleanup_cap():
    return FakeCleanup()


@pytest.fixture()
def agent(setup_cap, cleanup_cap):
    return HostAgent(setup_cap=setup_cap, cleanup_cap=cleanup_cap)


# ─── Dispatch routes setup correctly ─────────────────────────────────


class TestDispatchSetup:
    def test_setup_routes_to_setup_cap(self, agent, setup_cap):
        req = HostRequest(action="setup", subdir=SkillSubdir("implement"))
        result = agent.dispatch(req)

        assert setup_cap.calls == [SkillSubdir("implement")]
        assert result.scratch_dir == "/tmp/implement"


# ─── Dispatch routes cleanup correctly ───────────────────────────────


class TestDispatchCleanup:
    def test_cleanup_routes_to_cleanup_cap(self, agent, cleanup_cap):
        req = HostRequest(action="cleanup", paths=["/a.txt", "/b.txt"])
        result = agent.dispatch(req)

        assert cleanup_cap.calls == [["/a.txt", "/b.txt"]]
        assert result.failed_count == 0


# ─── Unknown action → HostError ──────────────────────────────────────


class TestDispatchUnknownAction:
    def test_raises_host_error_not_valueerror(self, agent):
        req = HostRequest(action="bogus", subdir=SkillSubdir("implement"))

        with pytest.raises(HostError) as exc_info:
            agent.dispatch(req)

        assert "host: unknown action" in str(exc_info.value)


# ─── paths None vs empty list guard ──────────────────────────────────


class TestPathsNoneGuard:
    def test_paths_none_treated_as_empty(self, agent, cleanup_cap):
        # request.paths is None → should pass [] not None to cleanup
        req = HostRequest(action="cleanup", subdir=SkillSubdir("implement"), paths=None)
        agent.dispatch(req)

        assert cleanup_cap.calls == [[]]


# ─── Constructor injection via create() ──────────────────────────────


class TestCreateConstructorInjection:
    def test_create_uses_injected_capabilities(self, setup_cap, cleanup_cap):
        agent = HostAgent.create(setup_cap=setup_cap, cleanup_cap=cleanup_cap)

        assert isinstance(agent, HostAgent)
        assert agent._setup is setup_cap
        assert agent._cleanup is cleanup_cap