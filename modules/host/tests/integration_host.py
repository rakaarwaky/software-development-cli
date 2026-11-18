"""Integration tests for host module and DI wiring.

Proves: module / crate / package + DI wiring.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cli.src.surface_sdc_command import reset_capabilities, set_capabilities
from host.src.agent_host_orchestrator import HostAgent
from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup
from host.src.capabilities_host_setup import CapabilitiesHostSetup
from shared.src.host.contract_host_aggregate import IHostAggregate


class TestHostDIWiring:
    """Host capabilities wired through root container and surface."""

    def test_root_container_wires_all_capabilities(self) -> None:
        from host.src.root_host_container import HostContainer

        container = HostContainer()
        assert isinstance(container.aggregate, IHostAggregate)

    def test_set_capabilities_accepts_host_aggregate(self) -> None:
        reset_capabilities()
        host = HostAgent(
            setup_cap=CapabilitiesHostSetup(),
            cleanup_cap=CapabilitiesHostCleanup(),
        )
        set_capabilities(
            host=host,
            memory=MagicMock(),
            planner=MagicMock(),
        )

    def test_root_container_create_host_feature_is_callable(self) -> None:
        from host.src.root_host_container import create_host_feature

        feature = create_host_feature()
        assert callable(getattr(feature, "dispatch", None))