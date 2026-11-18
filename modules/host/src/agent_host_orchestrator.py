"""Host agent orchestrator (AES agent layer).

Routes host requests to the correct capability: setup or cleanup.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.host.contract_host_aggregate import IHostAggregate
from shared.src.host.contract_host_protocol import (
    IHostCleanupProtocol,
    IHostSetupProtocol,
)
from shared.src.host.taxonomy_host_request import HostAction, HostRequest, HostResult

# ─── Block 1: Module Declaration ───────────────────────────────────────

_SETUP_ACTION = HostAction("setup")
_CLEANUP_ACTION = HostAction("cleanup")


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
        if request.action == _SETUP_ACTION:
            return self._setup.setup(request.subdir)
        if request.action == _CLEANUP_ACTION:
            paths = request.paths if request.paths is not None else []
            return self._cleanup.cleanup(paths)
        raise HostError(
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