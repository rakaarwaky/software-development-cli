"""Host helper shared utility (AES utility layer).

Stateless helpers shared across the three per-skill host capabilities
(implement, design, execute). Lives in the shared kernel so the
per-skill capability files in ``modules/host/src/`` stay thin and free
of duplication (AES305).

No class definitions, no state — pure functions only (AES404).
"""

from __future__ import annotations

import stat
import sys
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
from shared.src.host.taxonomy_host_request import HostResult

_VALID_SUBDIRS = (
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
    SKILL_SUBDIR_EXECUTE,
)


def resolve_subdir(subdir: str) -> str:
    """Validate ``subdir`` is one of the known per-skill artifact subdirs.

    Raises ``HostError`` on unknown values.
    """
    if subdir not in _VALID_SUBDIRS:
        raise HostError(
            f"host: unknown subdir {subdir!r}; expected one of {_VALID_SUBDIRS!r}"
        )
    return subdir


def make_scratch_dir(subdir: str) -> Path:
    """Return ``~/.agents/develop/<reponame>/<subdir>/`` (mode ``0o700``).

    Raises ``HostError`` when the repo slug cannot be resolved.
    """
    path = develop_root() / repo_slug() / subdir
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(stat.S_IRWXU)
    except OSError:
        pass
    return path


def make_setup_result(subdir: str) -> HostResult:
    """Build a ``HostResult`` for a ``setup`` request on ``subdir``."""
    scratch = make_scratch_dir(subdir)
    return HostResult(
        python=resolve_python(),
        scratch_dir=str(scratch),
        run_id=str(uuid.uuid4().hex[:8]),
    )


def make_cleanup_result(paths: list[str]) -> HostResult:
    """Unlink each path; missing paths are skipped silently.

    Returns a ``HostResult`` with ``failed_count`` set.
    """
    failed = 0
    for raw in paths:
        try:
            Path(raw).unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"host: could not remove {raw}: {exc}", file=sys.stderr)
            failed += 1
    return HostResult(failed_count=failed)