"""Host composition root — wires setup and cleanup capabilities into HostAgent."""

from __future__ import annotations

from shared.src.host.contract_host_aggregate import IHostAggregate

from modules.host.src.agent_host_orchestrator import HostAgent
from modules.host.src.capabilities_host_cleanup import CapabilitiesHostCleanup
from modules.host.src.capabilities_host_setup import CapabilitiesHostSetup


class HostContainer:
    """Construct the host capabilities and orchestrator (wiring only)."""

    def __init__(self) -> None:
        self._orchestrator = HostAgent(
            setup_cap=CapabilitiesHostSetup(),
            cleanup_cap=CapabilitiesHostCleanup(),
        )

    @property
    def aggregate(self) -> IHostAggregate:
        return self._orchestrator


def create_host_feature() -> IHostAggregate:
    """Fully-wired host feature aggregate (factory for entry / DI)."""
    return HostContainer().aggregate