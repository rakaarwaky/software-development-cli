"""Host-domain aggregate contract (AES contract layer, ABC trait).

Single entry point for the host agent orchestrator: dispatch a
``HostRequest`` to the right per-skill capability by ``subdir``.
The agent layer calls ``dispatch`` with a ``HostRequest`` and a
``subdir`` and gets a ``HostResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.host.taxonomy_host_request import HostRequest, HostResult


class IHostAggregate(ABC):
    """Single entry point over the host agent orchestrator."""

    @abstractmethod
    def dispatch(self, request: HostRequest, *, subdir: str) -> HostResult:
        """Route the host request to the correct capability by ``subdir``."""
        ...