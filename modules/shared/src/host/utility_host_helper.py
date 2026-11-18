"""Host helper shared utility (AES utility layer).

Stateless helpers shared across the three per-skill host capabilities
(implement, planner, execute). Lives in the shared kernel so the
per-skill capability files in ``modules/host/src/`` stay thin and free
of duplication (AES305).

No class definitions, no state — pure functions only (AES404).
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess  # nosec: trusted system git/python calls
import sys
import uuid
from pathlib import Path

from shared.src.common.taxonomy_sdc_constant import (
    DEVELOP_ROOT_DIRNAME,
    DEVELOP_ROOT_SUBDIR,
    GIT_TIMEOUT_SECONDS,
    SKILL_SUBDIR_EXECUTE,
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
)
from shared.src.common.taxonomy_sdc_error import HostError
from shared.src.host.taxonomy_host_request import HostResult


def _git_executable() -> str:
    """Return the absolute path to the git executable, or ``git`` as fallback."""
    found = shutil.which("git")
    return found if found is not None else "git"

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


def develop_root() -> Path:
    """Return ``~/.agents/develop``."""
    return Path.home() / DEVELOP_ROOT_DIRNAME / DEVELOP_ROOT_SUBDIR


def repo_slug() -> str:
    """Return the git repository slug (from remote origin, else git toplevel dir name).

    Raises ``HostError`` when the current directory is not inside a git
    repository or the slug cannot be derived.
    """
    try:
        toplevel_result = subprocess.run(  # nosec: git args are internally built
            [_git_executable(), "rev-parse", "--show-toplevel"],
            capture_output=True,
            check=False,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        raise HostError("host: git command failed")

    if toplevel_result.returncode != 0 or not toplevel_result.stdout.strip():
        raise HostError("host: not inside a git repository")

    remote_name = _repo_name_from_remote()
    if remote_name:
        slug = _slugify(remote_name)
        if slug:
            return slug

    name = Path(toplevel_result.stdout.strip()).name
    slug = _slugify(name)
    if not slug:
        raise HostError("host: could not derive project repo name from git root")
    return slug


def resolve_python() -> str:
    """Return an absolute Python 3 executable. Linux only.

    Raises ``HostError`` on non-Linux platforms or when no Python 3
    interpreter is found on PATH.
    """
    if os.name != "posix" or sys.platform != "linux":
        raise HostError("host: this helper runs on Linux only")
    current = sys.executable or ""
    if current and sys.version_info.major == 3:
        return current
    found = shutil.which("python3")
    if found:
        return found
    raise HostError("host: no Python 3 interpreter found")


def _repo_name_from_remote() -> str | None:
    """Extract the repository name from ``git remote get-url origin``.

    Strips ``.git`` suffix and path components so
    ``https://github.com/user/my-repo.git`` → ``my-repo``.
    Returns ``None`` when no origin remote is configured or git fails.
    """
    try:
        result = subprocess.run(  # nosec: git args are internally built
            [_git_executable(), "remote", "get-url", "origin"],
            capture_output=True,
            check=False,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    url = result.stdout.strip().rstrip("/")
    while url.endswith(".git"):
        url = url[:-4]
    if ":" in url and "//" not in url:
        url = url.rsplit(":", 1)[-1]
    name = url.rsplit("/", 1)[-1]
    return name if name else None


def _slugify(name: str) -> str:
    """Slugify ``name`` to lowercase-alphanumeric-plus-dash.

    Strips non-slug characters, collapses multiple dashes, and trims
    leading/trailing dashes. Returns the empty string when nothing
    survives (the caller raises ``HostError`` in that case).
    """
    import re

    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)


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
    """Unlink paths only under the managed ``~/.agents/develop`` root.

    Missing paths are skipped silently. Paths outside the managed root are
    rejected so a bad caller cannot delete arbitrary user files.
    """
    failed = 0
    root = develop_root().resolve()
    for raw in paths:
        try:
            path = Path(raw).expanduser().resolve()
            path.relative_to(root)
        except ValueError:
            print(
                f"host: refusing to remove path outside {root}: {raw}",
                file=sys.stderr,
            )
            failed += 1
            continue
        except OSError as exc:
            print(f"host: could not resolve {raw}: {exc}", file=sys.stderr)
            failed += 1
            continue

        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            print(f"host: could not remove {raw}: {exc}", file=sys.stderr)
            failed += 1
    return HostResult(failed_count=failed)