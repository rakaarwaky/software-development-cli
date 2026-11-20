"""Shared-kernel utilities for the sdc domain (AES common utility layer).

Stateless helpers consumed by more than one module domain. No stateful
objects, no class definitions, no contract impls.
"""

from __future__ import annotations

import re
import shutil
import stat
import subprocess  # nosec: trusted system git/python calls
import sys
from pathlib import Path

from shared.src.common.taxonomy_sdc_constant import (
    _SLUG_DASH_RE,
    _SLUG_INVALID_RE,
    CASE_INSENSITIVE_HOSTS,
    DEVELOP_ROOT_DIRNAME,
    DEVELOP_ROOT_SUBDIR,
    GIT_TIMEOUT_SECONDS,
    SSH_BARE_REMOTE_RE,
    SSH_REMOTE_RE,
    URL_REMOTE_RE,
)
from shared.src.common.taxonomy_sdc_error import HostError


def _git_executable() -> str:
    """Return the absolute path to the git executable, or ``git`` as fallback."""
    found = shutil.which("git")
    return found if found is not None else "git"


def bootstrap_ns_roots() -> None:
    """Ensure every module's ``src/`` AND its parent package root are on
    ``sys.path`` so both bare intra-module imports
    (``from shared.src...``, ``from cli.src...``) and test-worker imports
    (``from memory.src.capabilities_memory_writer import ...``) resolve.

    Called once at CLI entry before any module import that uses bare
    sibling imports. Idempotent and safe to call repeatedly.
    """
    modules_root = Path(__file__).resolve().parents[2]
    tools_root = modules_root.parent
    if str(tools_root) not in sys.path:
        sys.path.append(str(tools_root))
    if str(modules_root) not in sys.path:
        sys.path.append(str(modules_root))
    for _m in ("shared", "cli", "planner", "memory", "host", "pool"):
        _pkg = modules_root / _m
        if str(_pkg) not in sys.path:
            sys.path.append(str(_pkg))
        _src = _pkg / "src"
        if _src.is_dir():
            _p = str(_src)
            if _p not in sys.path:
                sys.path.append(_p)


def resolve_python() -> str:
    """Return an absolute Python 3 executable. Linux only.

    Raises ``HostError`` on non-Linux platforms or when no Python 3
    interpreter is found on PATH.
    """
    import os

    if os.name != "posix" or sys.platform != "linux":
        raise HostError("host: this helper runs on Linux only")
    current = sys.executable or ""
    if current and sys.version_info.major == 3:
        return current
    found = shutil.which("python3")
    if found:
        return found
    raise HostError("host: no Python 3 interpreter found")


def develop_root() -> Path:
    """Return ``~/.agents/develop``."""
    return Path.home() / DEVELOP_ROOT_DIRNAME / DEVELOP_ROOT_SUBDIR


def slugify(name: str) -> str:
    """Slugify ``name`` to lowercase-alphanumeric-plus-dash.

    Strips non-slug characters, collapses multiple dashes, and trims
    leading/trailing dashes. Returns the empty string when nothing
    survives (the caller raises ``HostError`` in that case).
    """
    slug = _SLUG_INVALID_RE.sub("-", name.lower()).strip("-")
    return _SLUG_DASH_RE.sub("-", slug)


def repo_name_from_remote() -> str | None:
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

    remote_name = repo_name_from_remote()
    if remote_name:
        slug = slugify(remote_name)
        if slug:
            return slug

    name = Path(toplevel_result.stdout.strip()).name
    slug = slugify(name)
    if not slug:
        raise HostError("host: could not derive project repo name from git root")
    return slug


def scratch_dir_for(subdir: str) -> Path:
    """Return the per-repo, per-skill artifact root ``~/.agents/develop/<slug>/<subdir>/``.

    Creates the directory (mode ``0o700``) if it does not exist.
    Raises ``HostError`` when the slug cannot be resolved.
    """
    path = develop_root() / repo_slug() / subdir
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(stat.S_IRWXU)
    except OSError:
        pass
    return path


def canonicalize_remote(url: str) -> str:
    """Normalise a git remote URL to a stable key.

    Collapses SSH / bare SSH / URL variants of the same upstream onto a
    single string. Host is always lowercased; path is lowercased for
    ``CASE_INSENSITIVE_HOSTS`` (github.com, gitlab.com, bitbucket.org).
    All trailing slashes and ``.git`` suffixes are stripped.
    """
    url = url.strip().rstrip("/")
    while url.endswith(".git"):
        url = url[:-4]
    m = SSH_REMOTE_RE.match(url)
    if m:
        host = m.group(1).lower()
        path = m.group(2)
        if host in CASE_INSENSITIVE_HOSTS:
            path = path.lower()
        return f"{host}/{path}"
    m = SSH_BARE_REMOTE_RE.match(url)
    if m:
        host = m.group(1).lower()
        path = m.group(2)
        if host in CASE_INSENSITIVE_HOSTS:
            path = path.lower()
        return f"{host}/{path}"
    m = URL_REMOTE_RE.match(url)
    if m:
        host = m.group(1).lower()
        path = m.group(2)
        if host in CASE_INSENSITIVE_HOSTS:
            path = path.lower()
        return f"{host}{path}"
    return url


def sanitize_one_line(text: str) -> str:
    """Collapse line-breaking whitespace to single spaces; strip outer whitespace."""
    return re.sub(r"[\r\n\t]+", " ", text).strip()


def normalize(text: str) -> str:
    """Collapse a description to a canonical form for dedup matching.

    Lowercase, strip trailing punctuation/whitespace, collapse internal
    whitespace runs to single spaces.
    """
    from shared.src.common.taxonomy_sdc_constant import (
        PUNCT_TAIL_RE,
        WHITESPACE_RE,
    )

    text = text.lower().strip()
    text = PUNCT_TAIL_RE.sub("", text)
    return WHITESPACE_RE.sub(" ", text)


def git_output(*args: str) -> str | None:
    """Run a git command and return stripped stdout, or None on failure."""
    try:
        result = subprocess.run(  # nosec: git args are internally built
            [_git_executable(), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    out = result.stdout.strip()
    return out or None