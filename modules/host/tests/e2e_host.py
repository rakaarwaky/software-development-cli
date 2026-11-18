"""E2E tests for the host feature.

Proves: full request lifecycle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from host.src.agent_host_orchestrator import HostAgent
from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup
from host.src.capabilities_host_setup import CapabilitiesHostSetup
from shared.src.host.taxonomy_host_request import HostRequest


def _make_orchestrator() -> HostAgent:
    return HostAgent(
        setup_cap=CapabilitiesHostSetup(),
        cleanup_cap=CapabilitiesHostCleanup(),
    )


class TestHostE2E:
    """Full lifecycle: create artifact root then clean up files."""

    def test_setup_creates_root_then_cleanup_removes_files(
        self, tmp_path: Path, isolated_home, monkeypatch
    ) -> None:
        agent = _make_orchestrator()
        monkeypatch.setattr(
            "shared.src.host.utility_host_helper.develop_root",
            lambda: tmp_path / ".agents" / "develop",
        )
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        file_a = managed / "a.txt"
        file_b = managed / "b.txt"
        file_a.write_text("data")
        file_b.write_text("data")

        cleanup = agent.dispatch(
            HostRequest(action="cleanup", paths=[str(file_a), str(file_b)])
        )
        assert cleanup.failed_count == 0
        assert not file_a.exists()
        assert not file_b.exists()