"""Memory-domain capability contracts (AES102 `_protocol`).

One file for the memory feature declaring 4 rich capability seams:
- IMemoryPathProtocol: resolves file/lock paths for the current repo
- IMemoryReaderProtocol: reads raw markdown content of the memory file
- IMemoryWriterProtocol: merges run patterns/specs under exclusive lock
- IMemoryTopProtocol: returns the top-N common issue patterns (read-only)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.common.taxonomy_sdc_vo import (
    MemoryContent,
    PatternCategory,
    PatternCount,
    RepoPaths,
)
from shared.src.memory.taxonomy_memory_request import (
    MemoryResult,
    UpdateSpec,
)


class IMemoryPathProtocol(ABC):
    """Path resolution capability seam for the memory file."""

    @abstractmethod
    def resolve_paths(self, *, create_dir: bool = False) -> RepoPaths:
        """Return the ``dir``/``file``/``lock``/``workspace_id`` paths for the active repository."""
        ...


class IMemoryReaderProtocol(ABC):
    """Raw content reading capability seam for the memory file."""

    @abstractmethod
    def read_content(self) -> MemoryContent:
        """Read and return raw memory markdown content, or empty string if missing."""
        ...


class IMemoryWriterProtocol(ABC):
    """Exclusive-lock update capability seam for the memory file."""

    @abstractmethod
    def update(self, spec: UpdateSpec) -> MemoryResult:
        """Merge a run spec into the memory file under exclusive lock; return stats."""
        ...


class IMemoryTopProtocol(ABC):
    """Read-only top-N patterns capability seam for the memory file."""

    @abstractmethod
    def top(
        self, n: PatternCount, category: PatternCategory | None = None
    ) -> MemoryResult:
        """Return the top-N common issue patterns (optionally filtered by category)."""
        ...


__all__ = [
    "IMemoryPathProtocol",
    "IMemoryReaderProtocol",
    "IMemoryTopProtocol",
    "IMemoryWriterProtocol",
]

_layer_symbols = {
    "IMemoryPathProtocol": IMemoryPathProtocol,
    "IMemoryReaderProtocol": IMemoryReaderProtocol,
    "IMemoryWriterProtocol": IMemoryWriterProtocol,
    "IMemoryTopProtocol": IMemoryTopProtocol,
}