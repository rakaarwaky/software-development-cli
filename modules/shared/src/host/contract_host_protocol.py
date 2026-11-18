"""Host-domain contract (AES contract layer, ABC trait).

Single protocol for the host helper capability: setup + cleanup.
The agent orchestrator calls ``execute`` with a ``HostRequest`` and
gets a ``HostResult`` back. Capabilities implement this protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.host.taxonomy_host_request import HostRequest, HostResult


class IHostProtocol(ABC):
    """Single protocol over the host helper capability.

    Implementations live in ``modules/host/src/capabilities_host_*.py``.
    """

    @abstractmethod
    def execute(self, request: HostRequest) -> HostResult:
        """Run the host operation; return the result."""
        ...