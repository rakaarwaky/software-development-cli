"""Pool-domain aggregate contract (AES contract layer, ABC trait).

Single entry point for the poll agent orchestrator: dispatch a
``PoolRequest`` to the right agent capability by agent kind. The
surface calls ``execute`` with a ``PoolRequest`` and gets a
``PoolResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.pool.taxonomy_pool_request import PoolRequest, PoolResult


class IPoolAggregate(ABC):
    """Single entry point over the poll agent orchestrator."""

    @abstractmethod
    def execute(self, request: PoolRequest) -> PoolResult:
        """Route the poll request to the correct capability; return the result."""
        ...
