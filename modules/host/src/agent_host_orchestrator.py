"""Host agent orchestrator (AES agent layer).

Routes host requests to the correct per-skill capability. The surface
calls the agent; the agent dispatches to the right capability.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_constant import SKILL_SUBDIR_EXECUTE
from shared.src.common.taxonomy_sdc_constant import SKILL_SUBDIR_IMPLEMENT
from shared.src.common.taxonomy_sdc_constant import SKILL_SUBDIR_PLAN
from shared.src.host.contract_host_aggregate import IHostAggregate
from shared.src.host.taxonomy_host_request import HostRequest, HostResult
from shared.src.host.utility_host_helper import (
    make_cleanup_result,
    make_setup_result,
    resolve_subdir,
)


# ─── Block 1: Module Declaration ───────────────────────────────────────

class HostAgent(IHostAggregate):
    """Agent orchestrator for the host feature.

    Composes the three per-skill capabilities and routes by subdir.
    """

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def dispatch(self, request: HostRequest, *, subdir: str) -> HostResult:
        """Route a host request to the right capability.

        Args:
            request: The host request.
            subdir: One of ``implement``, ``plan``, ``execute``, or ``""``
                (empty string routes cleanup to the implement capability).
        """
        if request.action == "setup":
            return self._setup(subdir)
        if request.action == "cleanup":
            return make_cleanup_result(request.paths or [])
        raise ValueError(
            f"host: unknown action {request.action!r}; expected 'setup' or 'cleanup'"
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def _setup(self, subdir: str) -> HostResult:
        """Build the setup result for ``subdir``."""
        if subdir == "plan":
            resolve_subdir(SKILL_SUBDIR_PLAN)
            return make_setup_result(SKILL_SUBDIR_PLAN)
        if subdir == "execute":
            resolve_subdir(SKILL_SUBDIR_EXECUTE)
            return make_setup_result(SKILL_SUBDIR_EXECUTE)
        resolve_subdir(SKILL_SUBDIR_IMPLEMENT)
        return make_setup_result(SKILL_SUBDIR_IMPLEMENT)