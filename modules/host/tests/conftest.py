"""Fixtures for host capability tests.

Provides temporary git repositories (with and without remote origin),
isolated develop roots, and shared helpers.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

_MODULES_ROOT = Path(__file__).resolve().parents[3]
for _m in ("shared", "cli", "planner", "memory", "host"):
    _src = _MODULES_ROOT / "modules" / _m / "src"
    if _src.is_dir() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
if str(_MODULES_ROOT / "modules") not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT / "modules"))

import pytest

from shared.src.common.taxonomy_sdc_constant import (
    SKILL_SUBDIR_EXECUTE,
    SKILL_SUBDIR_IMPLEMENT,
    SKILL_SUBDIR_PLAN,
)
from shared.src.common.taxonomy_sdc_vo import SkillSubdir


# ─── Isolated home / develop root ─────────────────────────────────────


@pytest.fixture()
def isolated_home(tmp_path, monkeypatch):
    """Isolate ``Path.home()`` to a temp directory.

    ``develop_root()`` resolves to ``<tmp_path>/.agents/develop/``.
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture()
def develop_root(isolated_home):
    """Return the isolated develop root: ``<tmp>/.agents/develop``."""
    root = isolated_home / ".agents" / "develop"
    root.mkdir(parents=True, exist_ok=True)
    return root


# ─── Temporary git repositories ───────────────────────────────────────


def _git_init(path: Path, origin_url: str | None = None) -> None:
    """Initialise a git repository at *path* with an optional origin remote."""
    subprocess.run(
        ["git", "init"],
        cwd=path,
        capture_output=True,
        check=True,
    )
    if origin_url is not None:
        subprocess.run(
            ["git", "remote", "add", "origin", origin_url],
            cwd=path,
            capture_output=True,
            check=True,
        )


@pytest.fixture()
def git_repo(tmp_path, monkeypatch):
    """A git repository WITH an origin remote (``my-repo``).

    ``repo_slug()`` will resolve to ``my-repo``.
    """
    repo = tmp_path / "my-repo"
    repo.mkdir()
    _git_init(repo, "https://github.com/user/my-repo.git")
    monkeypatch.chdir(repo)
    return repo


@pytest.fixture()
def git_repo_no_remote(tmp_path, monkeypatch):
    """A git repository WITHOUT an origin remote.

    ``repo_slug()`` falls back to the toplevel directory name ``norepo``.
    """
    repo = tmp_path / "norepo"
    repo.mkdir()
    _git_init(repo)
    monkeypatch.chdir(repo)
    return repo


@pytest.fixture()
def not_a_git_repo(tmp_path, monkeypatch):
    """A plain directory that is NOT a git repository."""
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)
    return plain


# ─── Valid / invalid subdir helpers ──────────────────────────────────


@pytest.fixture()
def valid_subdirs() -> tuple[str, ...]:
    return (
        SKILL_SUBDIR_IMPLEMENT,
        SKILL_SUBDIR_PLAN,
        SKILL_SUBDIR_EXECUTE,
    )


# ─── File cleanup helpers ─────────────────────────────────────────────


@pytest.fixture()
def existing_files(tmp_path):
    """Create N existing files under *tmp_path* and return their paths.

    Usage: ``existing_files(tmp_path, 3)``
    """
    paths = []
    for i in range(3):
        p = tmp_path / f"file_{i}.txt"
        p.write_text(f"content {i}")
        paths.append(str(p))
    return paths


@pytest.fixture()
def existing_directory(tmp_path):
    """Create a directory (not a regular file) and return its path."""
    d = tmp_path / "a_directory"
    d.mkdir()
    return str(d)


# ─── Mode helpers ─────────────────────────────────────────────────────


@pytest.fixture()
def check_mode():
    """Return a helper that checks a directory's mode is ``0o700``."""

    def _check(path: Path) -> None:
        mode = stat.S_IMODE(path.stat().st_mode)
        assert mode == 0o700, f"expected 0o700, got {oct(mode)}"

    return _check