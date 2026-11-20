"""Pool-domain capability contracts (AES contract layer, ABC).

One rich capability seam for the agent-session poller:
  IPoolGrokProtocol — poll a Grok Build session in an Orca terminal
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.pool.taxonomy_pool_request import PoolRequest, PoolResult


class IPoolGrokProtocol(ABC):
    """Capability seam that polls a Grok Build Orca terminal session."""

    @abstractmethod
    def poll(self, request: PoolRequest) -> PoolResult:
        """Probe the session once, or block until completion/deadline."""
        ...


__all__ = [
    "IPoolGrokProtocol",
]

_layer_symbols = {
    "IPoolGrokProtocol": IPoolGrokProtocol,
}
