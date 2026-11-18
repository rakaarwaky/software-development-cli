"""Memory agent orchestrator (AES agent layer).

Single entry point for memory operations. The surface calls the agent;
the agent dispatches to the memory capability. Kept as a distinct layer
so the surface depends on an aggregate seam (``IMemoryAggregate``).
"""

from __future__ import annotations

from shared.src.memory.contract_memory_aggregate import IMemoryAggregate
from shared.src.memory.contract_memory_protocol import IMemoryProtocol
from shared.src.memory.taxonomy_memory_request import MemoryRequest, MemoryResult


# ─── Block 1: Module Declaration ───────────────────────────────────────

class MemoryAgent(IMemoryAggregate):
    """Agent orchestrator for the memory feature.

    Composes the memory manager capability and routes every request
    through it via the ``IMemoryProtocol`` seam.
    """

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def __init__(self, store: IMemoryProtocol) -> None:
        self._store = store

    def execute(self, request: MemoryRequest) -> MemoryResult:
        """Route a memory request to the memory manager capability."""
        return self._store.execute(request)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return f"MemoryAgent(store={self._store!r})"