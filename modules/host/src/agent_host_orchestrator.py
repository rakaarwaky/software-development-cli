"""Host agent orchestrator (AES agent layer).

Routes host requests to the correct capability: setup or cleanup.
"""

from __future__ import annotations

from shared.src.host.contract_host_aggregate import IHostAggregate
from shared.src.host.contract_host_protocol import (
    IHostCleanupProtocol,
    IHostSetupProtocol,
)
from shared.src.host.taxonomy_host_request import HostRequest, HostResult

# ─── Block 1: Module Declaration ───────────────────────────────────────


class HostAgent(IHostAggregate):
    """Agent orchestrator for the host feature.

    Dispatches host actions (setup, cleanup) to their respective capabilities.
    """

    def __init__(
        self,
        setup_cap: IHostSetupProtocol,
        cleanup_cap: IHostCleanupProtocol,
    ) -> None:
        self._setup = setup_cap
        self._cleanup = cleanup_cap

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def dispatch(self, request: HostRequest) -> HostResult:
        if request.action == "setup":
            return self._setup.setup(request.subdir)
        if request.action == "cleanup":
            return self._cleanup.cleanup(request.paths or [])
        raise ValueError(
            f"host: unknown action {request.action!r}; expected 'setup' or 'cleanup'"
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create(
        cls,
        setup_cap: IHostSetupProtocol,
        cleanup_cap: IHostCleanupProtocol,
    ) -> HostAgent:
        return cls(
            setup_cap=setup_cap,
            cleanup_cap=cleanup_cap,
        )

    def __repr__(self) -> str:
        return "HostAgent()"