"""Host-domain contract (AES contract layer, ABC trait).

Single entry point over the host helper capability: setup + cleanup.
The CLI surface calls ``execute`` with a ``HostRequest`` and gets a
``HostResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.host.taxonomy_host_request import HostRequest, HostResult


class IHostAggregate(ABC):
    """Single entry point over the host helper capability."""

    @abstractmethod
    def execute(self, request: HostRequest) -> HostResult:
        """Run the host operation the surface asked for; return the result."""
        ...