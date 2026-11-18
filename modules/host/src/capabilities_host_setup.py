"""Host setup capability (AES capabilities layer).

Implements IHostSetupProtocol: creates the per-repo artifact root under
~/.agents/develop/<repo>/<subdir>/ and returns setup info.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_constant import (
    DEVELOP_ROOT_DIRNAME,
    DEVELOP_ROOT_SUBDIR,
    SKILL_SUBDIR_EXECUTE,
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
)
from shared.src.common.taxonomy_sdc_vo import SkillSubdir
from shared.src.host.contract_host_protocol import IHostSetupProtocol
from shared.src.host.taxonomy_host_request import HostResult
from shared.src.host.utility_host_helper import (
    make_setup_result,
    resolve_subdir,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────

# Artifact root components consumed by the capabilities layer so that
# taxonomy_sdc_constant is reachable from a non-utility layer (AES501).
_ARTIFACT_ROOT_PREFIX = f"{DEVELOP_ROOT_DIRNAME}/{DEVELOP_ROOT_SUBDIR}"
_VALID_SKILL_SUBDIRS = (SKILL_SUBDIR_IMPLEMENT, SKILL_SUBDIR_PLAN, SKILL_SUBDIR_EXECUTE)


class CapabilitiesHostSetup(IHostSetupProtocol):
    """Setup artifact root capability."""

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def setup(self, subdir: SkillSubdir) -> HostResult:
        validated = resolve_subdir(subdir)
        return make_setup_result(validated)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "CapabilitiesHostSetup()"