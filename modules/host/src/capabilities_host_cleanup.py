"""Host cleanup capability (AES capabilities layer).

Implements IHostCleanupProtocol: unlinks file paths, skipping missing ones.
"""

from __future__ import annotations

from shared.src.host.contract_host_protocol import IHostCleanupProtocol
from shared.src.host.taxonomy_host_request import HostResult
from shared.src.host.utility_host_helper import make_cleanup_result

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesHostCleanup(IHostCleanupProtocol):
    """Cleanup paths capability."""

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def cleanup(self, paths: list[str]) -> HostResult:
        return make_cleanup_result(paths)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "CapabilitiesHostCleanup()"