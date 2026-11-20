"""Pool composition root — wires the Grok capability into AgentPool."""

from __future__ import annotations

from shared.src.pool.contract_pool_aggregate import IPoolAggregate

from modules.pool.src.agent_pool_orchestrator import AgentPool
from modules.pool.src.capabilities_pool_grok import CapabilitiesPoolGrok


class PoolContainer:
    """Construct the pool capability and orchestrator (wiring only)."""

    def __init__(self) -> None:
        self._aggregate = AgentPool(
            grok_cap=CapabilitiesPoolGrok.create_default(),
        )

    @property
    def aggregate(self) -> IPoolAggregate:
        return self._aggregate


def create_pool_feature() -> IPoolAggregate:
    """Fully-wired pool feature aggregate (factory for entry / DI)."""
    return PoolContainer().aggregate
