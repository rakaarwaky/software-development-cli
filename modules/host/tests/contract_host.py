"""Contract tests for host protocols.

Verifies that host capabilities implement their protocol interfaces:
- IHostSetupProtocol
- IHostCleanupProtocol
- IHostAggregate
"""

from __future__ import annotations

from shared.src.host.contract_host_aggregate import IHostAggregate
from shared.src.host.contract_host_protocol import (
    IHostCleanupProtocol,
    IHostSetupProtocol,
)


class TestIHostSetupProtocol:
    """IHostSetupProtocol contract: setup method exists."""

    def test_capabilities_host_setup_implements_protocol(self) -> None:
        from host.src.capabilities_host_setup import CapabilitiesHostSetup

        cap = CapabilitiesHostSetup()
        assert isinstance(cap, IHostSetupProtocol)

    def test_capabilities_host_setup_has_setup_method(self) -> None:
        from host.src.capabilities_host_setup import CapabilitiesHostSetup

        cap = CapabilitiesHostSetup()
        assert hasattr(cap, "setup")
        assert callable(cap.setup)


class TestIHostCleanupProtocol:
    """IHostCleanupProtocol contract: cleanup method exists."""

    def test_capabilities_host_cleanup_implements_protocol(self) -> None:
        from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup

        cap = CapabilitiesHostCleanup()
        assert isinstance(cap, IHostCleanupProtocol)

    def test_capabilities_host_cleanup_has_cleanup_method(self) -> None:
        from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup

        cap = CapabilitiesHostCleanup()
        assert hasattr(cap, "cleanup")
        assert callable(cap.cleanup)


class TestIHostAggregate:
    """IHostAggregate contract: dispatch method exists."""

    def test_agent_host_orchestrator_implements_aggregate(self) -> None:
        from host.src.agent_host_orchestrator import HostAgent
        from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup
        from host.src.capabilities_host_setup import CapabilitiesHostSetup

        agent = HostAgent(
            setup_cap=CapabilitiesHostSetup(),
            cleanup_cap=CapabilitiesHostCleanup(),
        )
        assert isinstance(agent, IHostAggregate)

    def test_agent_host_orchestrator_has_dispatch_method(self) -> None:
        from host.src.agent_host_orchestrator import HostAgent
        from host.src.capabilities_host_cleanup import CapabilitiesHostCleanup
        from host.src.capabilities_host_setup import CapabilitiesHostSetup

        agent = HostAgent(
            setup_cap=CapabilitiesHostSetup(),
            cleanup_cap=CapabilitiesHostCleanup(),
        )
        assert hasattr(agent, "dispatch")
        assert callable(agent.dispatch)


class TestRootContainerContract:
    """Root container exposes IHostAggregate."""

    def test_create_host_feature_returns_aggregate(self) -> None:
        from host.src.root_host_container import create_host_feature

        feature = create_host_feature()
        assert isinstance(feature, IHostAggregate)