"""Memory-domain capability contracts (AES102 `_protocol`).

One file for the memory feature declaring 4 rich capability seams:
- IMemoryPathProtocol: resolves file/lock paths for the current repo
- IMemoryReaderProtocol: reads raw markdown content of the memory file
- IMemorySnapshotProtocol: parses and returns structured snapshot data
- IMemoryWriterProtocol: merges run patterns/specs under exclusive lock
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from shared.src.common.taxonomy_sdc_vo import MemoryContent
from shared.src.memory.taxonomy_memory_request import MemoryResult


class IMemoryPathProtocol(ABC):
    """Path resolution capability seam for the memory file."""

    @abstractmethod
    def resolve_paths(self, *, create_dir: bool = False) -> dict[str, Path]:
        """Return {"dir", "file", "lock"} for the active repository."""
        ...


class IMemoryReaderProtocol(ABC):
    """Raw content reading capability seam for the memory file."""

    @abstractmethod
    def read_content(self) -> MemoryContent:
        """Read and return raw memory markdown content, or empty string if missing."""
        ...


class IMemorySnapshotProtocol(ABC):
    """Structured parsing capability seam for the memory file."""

    @abstractmethod
    def read_snapshot(self) -> dict[str, Any]:
        """Parse and return {"common_issues": [...], "recent_runs": [...], "exists": bool}."""
        ...


class IMemoryWriterProtocol(ABC):
    """Exclusive-lock update capability seam for the memory file."""

    @abstractmethod
    def update(self, spec: dict[str, Any]) -> MemoryResult:
        """Merge a run spec into the memory file under exclusive lock; return stats."""
        ...


__all__ = [
    "IMemoryPathProtocol",
    "IMemoryReaderProtocol",
    "IMemorySnapshotProtocol",
    "IMemoryWriterProtocol",
]

_layer_symbols = {
    "IMemoryPathProtocol": IMemoryPathProtocol,
    "IMemoryReaderProtocol": IMemoryReaderProtocol,
    "IMemorySnapshotProtocol": IMemorySnapshotProtocol,
    "IMemoryWriterProtocol": IMemoryWriterProtocol,
}
