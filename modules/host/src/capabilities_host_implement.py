"""Host helper capability — implement skill (AES capabilities layer).

Implements ``IHostAggregate`` for the ``implement`` subdir. Delegates to
the shared utility layer (``utility_host_helper``) for all logic.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_constant import SKILL_SUBDIR_IMPLEMENT
from shared.src.host.contract_host_aggregate import IHostAggregate
from shared.src.host.taxonomy_host_request import HostRequest, HostResult
from shared.src.host.utility_host_helper import (
    make_cleanup_result,
    make_setup_result,
    resolve_subdir,
)


# ─── Block 1: Module Declaration ───────────────────────────────────────

class HostImplement(IHostAggregate):
    """Host capability for the ``implement`` skill subdir."""

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def execute(self, request: HostRequest) -> HostResult:
        """Route the request to the implement-specific host helper."""
        if request.action == "setup":
            resolve_subdir(SKILL_SUBDIR_IMPLEMENT)
            return make_setup_result(SKILL_SUBDIR_IMPLEMENT)
        if request.action == "cleanup":
            return make_cleanup_result(request.paths or [])
        raise ValueError(
            f"host: unknown action {request.action!r}; expected 'setup' or 'cleanup'"
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "HostImplement()"