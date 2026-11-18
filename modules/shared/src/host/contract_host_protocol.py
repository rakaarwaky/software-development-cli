"""Host-domain capability contracts (AES contract layer, ABC).

Two rich capability seams for the host helper feature:
  IHostSetupProtocol   — create the per-repo artifact root and return setup info
  IHostCleanupProtocol — unlink file paths, skipping missing ones
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.host.taxonomy_host_request import HostResult


class IHostSetupProtocol(ABC):
    """Setup artifact root capability seam."""

    @abstractmethod
    def setup(self, subdir: str) -> HostResult:
        """Create ~/.agents/develop/<repo>/<subdir>/ and return setup info."""
        ...


class IHostCleanupProtocol(ABC):
    """Cleanup paths capability seam."""

    @abstractmethod
    def cleanup(self, paths: list[str]) -> HostResult:
        """Unlink each path; missing paths are skipped silently."""
        ...


__all__ = [
    "IHostCleanupProtocol",
    "IHostSetupProtocol",
]

_layer_symbols = {
    "IHostCleanupProtocol": IHostCleanupProtocol,
    "IHostSetupProtocol": IHostSetupProtocol,
}