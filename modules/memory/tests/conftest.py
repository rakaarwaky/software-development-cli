"""Fixtures for memory capability tests.

Provides temporary git repositories, isolated home environments, and memory paths.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


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
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate ``Path.home()`` to a temp directory."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


@pytest.fixture()
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git repository WITH an origin remote."""
    repo = tmp_path / "my-memory-repo"
    repo.mkdir()
    _git_init(repo, "https://github.com/user/my-memory-repo.git")
    monkeypatch.chdir(repo)
    return repo
