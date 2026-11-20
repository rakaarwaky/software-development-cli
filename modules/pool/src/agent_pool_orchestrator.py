"""Pool agent orchestrator (AES agent layer).

Receives a PoolRequest, validates it, and dispatches to the owning
Grok capability seam. Returns a PoolResult. Pure dispatch — no I/O,
no computation of its own.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_error import PoolUsageError
from shared.src.pool.contract_pool_aggregate import IPoolAggregate
from shared.src.pool.contract_pool_protocol import IPoolGrokProtocol
from shared.src.pool.taxonomy_pool_constant import VALID_POOL_AGENTS
from shared.src.pool.taxonomy_pool_request import PoolRequest, PoolResult

# ─── Block 1: Module Declaration ──────────────────────────────────────


_POOL_ACTION = "poll"


class AgentPool(IPoolAggregate):
    """Agent orchestrator for the pool feature.

    Routes pool requests to the Grok capability seam (this single-agent
    feature owns exactly one protocol seam).
    """

    def __init__(self, grok_cap: IPoolGrokProtocol) -> None:
        self._grok = grok_cap

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def execute(self, request: PoolRequest) -> PoolResult:
        if request.action != _POOL_ACTION:
            raise PoolUsageError(
                f"pool: unknown action {request.action!r}; expected 'poll'"
            )
        if request.agent not in VALID_POOL_AGENTS:
            raise PoolUsageError(
                f"pool: unknown agent {request.agent!r}; "
                f"expected one of {VALID_POOL_AGENTS!r}"
            )
        return self._grok.poll(request)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create(cls, grok_cap: IPoolGrokProtocol) -> AgentPool:
        return cls(grok_cap=grok_cap)

    def __repr__(self) -> str:
        return "AgentPool()"
