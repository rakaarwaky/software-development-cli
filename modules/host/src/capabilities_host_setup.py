"""Host setup capability (AES capabilities layer).

Implements IHostSetupProtocol: creates the per-repo artifact root under
~/.agents/develop/<repo>/<subdir>/ and returns setup info.
"""

from __future__ import annotations

from shared.src.host.contract_host_protocol import IHostSetupProtocol
from shared.src.host.taxonomy_host_request import HostResult
from shared.src.host.utility_host_helper import (
    make_setup_result,
    resolve_subdir,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesHostSetup(IHostSetupProtocol):
    """Setup artifact root capability."""

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def setup(self, subdir: str) -> HostResult:
        resolve_subdir(subdir)
        return make_setup_result(subdir)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "CapabilitiesHostSetup()"