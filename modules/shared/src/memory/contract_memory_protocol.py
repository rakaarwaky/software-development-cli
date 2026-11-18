"""Memory-domain protocol contract (AES contract layer, ABC trait).

Single protocol for the memory manager capability: path, read, snapshot,
update. The agent orchestrator calls ``execute`` with a ``MemoryRequest``
and gets a ``MemoryResult`` back. Capabilities implement this protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.memory.taxonomy_memory_request import MemoryRequest, MemoryResult


class IMemoryProtocol(ABC):
    """Single protocol over the memory manager capability."""

    @abstractmethod
    def execute(self, request: MemoryRequest) -> MemoryResult:
        """Run the memory operation; return the result."""
        ...