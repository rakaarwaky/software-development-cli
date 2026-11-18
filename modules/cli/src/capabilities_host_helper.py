"""Host helper capability (AES capabilities layer).

Ported from the per-skill ``scripts/host.py`` (implement / design /
execute-plan variants). Collapses the three near-identical copies into
one capability that takes the per-skill ``subdir`` as a parameter
(``implement`` / ``plan`` / ``execute``).

Implements the ``IHostAggregate`` contract.
"""

from __future__ import annotations

import stat
import uuid
from pathlib import Path

from shared.src.common.taxonomy_sdc_constant import (
    SKILL_SUBDIR_EXECUTE,
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
)
from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.common.utility_sdc_common import (
    develop_root,
    repo_slug,
    resolve_python,
)
from shared.src.host.contract_host_aggregate import IHostAggregate
from shared.src.host.taxonomy_host_request import HostRequest, HostResult


class HostHelper(IHostAggregate):
    """Concrete host helper implementing ``IHostAggregate``."""

    def execute(self, request: HostRequest) -> HostResult:
        if request.action == "setup":
            sub = _validate_subdir(request.subdir)
            scratch = _scratch_dir_for(sub)
            return HostResult(
                python=resolve_python(),
                scratch_dir=str(scratch),
                run_id=str(uuid.uuid4().hex[:8]),
            )
        if request.action == "cleanup":
            failed = _cleanup(request.paths or [])
            return HostResult(failed_count=failed)
        raise HostError(
            f"host: unknown action {request.action!r}; expected 'setup' or 'cleanup'"
        )


# ─── Block 1: Module Declaration ───────────────────────────────────────

_SKILL_SUBDIRS = (
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
    SKILL_SUBDIR_EXECUTE,
)


def _validate_subdir(subdir: str) -> str:
    if subdir not in _SKILL_SUBDIRS:
        raise HostError(
            f"host: unknown subdir {subdir!r}; expected one of "
            f"{SKILL_SUBDIR_IMPLEMENT!r}, {SKILL_SUBDIR_PLAN!r}, {SKILL_SUBDIR_EXECUTE!r}"
        )
    return subdir


# ─── Block 2: Module Contract ──────────────────────────────────────────

# (Implemented inline in HostHelper.execute above.)


# ─── Block 3: Module Helpers ───────────────────────────────────────────


def _scratch_dir_for(subdir: str) -> Path:
    """Return ``~/.agents/develop/<reponame>/<subdir>/`` (mode ``0o700``)."""
    path = develop_root() / repo_slug() / subdir
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(stat.S_IRWXU)
    except OSError:
        pass
    return path


def _cleanup(paths: list[str]) -> int:
    """Unlink each path; missing paths are skipped silently.

    Returns the number of unlink failures.
    """
    failed = 0
    for raw in paths:
        try:
            Path(raw).unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"host: could not remove {raw}: {exc}")
            failed += 1
    return failed