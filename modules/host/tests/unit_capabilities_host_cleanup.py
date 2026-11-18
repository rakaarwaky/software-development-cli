"""Tests for CapabilitiesHostCleanup.

Covers FRD FR-HOST-002 test cases:
- All paths exist → removed, exit code 0
- Some missing → skipped, exit code 0
- One path is a directory → unlink fails, reported to stderr, exit code 1
- All paths missing → no removal, exit code 0
- Exact error message: ``host: could not remove <path>: <os error>`` on stderr
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.src.host.taxonomy_host_request import HostResult
from shared.src.host.utility_host_helper import make_cleanup_result


# ─── Fixtures ────────────────────────────────────────────────────────


# ─── FR-HOST-002: All paths exist ────────────────────────────────────

class TestCleanupAllExisting:
    """All paths exist → removed, exit code 0."""

    def test_removes_all_files(self, tmp_path, existing_files, isolated_home, monkeypatch):
        monkeypatch.setattr("shared.src.host.utility_host_helper.develop_root", lambda: tmp_path / ".agents" / "develop")
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        managed_files = []
        for i, _ in enumerate(existing_files):
            p = managed / f"file_{i}.txt"
            p.write_text("data")
            managed_files.append(str(p))

        result = make_cleanup_result(managed_files)

        assert result.failed_count == 0
        for p in managed_files:
            assert not Path(p).exists()


# ─── FR-HOST-002: Some paths missing ────────────────────────────────


class TestCleanupSomeMissing:
    """Some missing → skipped, remaining removed, exit code 0."""

    def test_skips_missing_paths(self, tmp_path, isolated_home, monkeypatch):
        monkeypatch.setattr("shared.src.host.utility_host_helper.develop_root", lambda: tmp_path / ".agents" / "develop")
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        existing = managed / "exists.txt"
        existing.write_text("data")
        missing = str(managed / "does_not_exist.txt")

        result = make_cleanup_result([str(existing), missing])

        assert result.failed_count == 0
        assert not existing.exists()


# ─── FR-HOST-002: One path is a directory ────────────────────────────


class TestCleanupDirectory:
    """One path is a directory → unlink fails, reported to stderr."""

    def test_directory_unlink_fails(
        self, tmp_path, capsys, existing_directory, isolated_home, monkeypatch
    ):
        monkeypatch.setattr(
            "shared.src.host.utility_host_helper.develop_root",
            lambda: tmp_path / ".agents" / "develop",
        )
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        file_path = managed / "file.txt"
        file_path.write_text("data")
        directory = managed / "dir"
        directory.mkdir()

        result = make_cleanup_result([str(file_path), str(directory)])

        assert result.failed_count == 1
        assert not file_path.exists()

        captured = capsys.readouterr()
        assert f"host: could not remove {directory}:" in captured.err


# ─── FR-HOST-002: All paths missing ──────────────────────────────────


class TestCleanupAllMissing:
    """All paths missing → no removal, exit code 0."""

    def test_no_output_no_failures(self, tmp_path, isolated_home, monkeypatch):
        monkeypatch.setattr(
            "shared.src.host.utility_host_helper.develop_root",
            lambda: tmp_path / ".agents" / "develop",
        )
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        missing1 = str(managed / "a.txt")
        missing2 = str(managed / "b.txt")

        result = make_cleanup_result([missing1, missing2])

        assert result.failed_count == 0


# ─── FR-HOST-002 Metric: Partial failure visibility ──────────────────


class TestCleanupPartialFailureVisibility:
    """Every failure reported to stderr."""

    def test_each_failure_reported(
        self, tmp_path, capsys, existing_directory, isolated_home, monkeypatch
    ):
        monkeypatch.setattr(
            "shared.src.host.utility_host_helper.develop_root",
            lambda: tmp_path / ".agents" / "develop",
        )
        managed = tmp_path / ".agents" / "develop" / "unit"
        managed.mkdir(parents=True)
        file_path = managed / "file.txt"
        file_path.write_text("data")
        directory = managed / "dir"
        directory.mkdir()

        result = make_cleanup_result([str(directory), str(file_path)])

        captured = capsys.readouterr()
        assert f"host: could not remove {directory}:" in captured.err
        assert result.failed_count == 1


# ─── FR-HOST-002: Empty paths list ───────────────────────────────────


class TestCleanupEmpty:
    """Zero paths → no failures."""

    def test_no_paths(self, tmp_path, capsys):
        result = make_cleanup_result([])

        assert result.failed_count == 0
        captured = capsys.readouterr()
        assert captured.err == ""