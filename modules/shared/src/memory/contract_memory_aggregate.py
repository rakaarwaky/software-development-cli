"""Memory-domain contract (AES contract layer, ABC trait).

Single entry point over the memory store capability: path, read, top,
update. The CLI surface calls ``execute`` with a ``MemoryRequest`` and
gets a ``MemoryResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.memory.taxonomy_memory_request import MemoryRequest, MemoryResult


class IMemoryAggregate(ABC):
    """Single entry point over the memory store capability."""

    @abstractmethod
    def execute(self, request: MemoryRequest) -> MemoryResult:
        """Run the memory operation the surface asked for; return the result."""
        ...