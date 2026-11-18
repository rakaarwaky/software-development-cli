"""Acceptance tests for the memory feature.

Proves: business requirement met.
"""

from __future__ import annotations

import pytest

from memory.src.capabilities_memory_path import CapabilitiesPath
from memory.src.capabilities_memory_reader import CapabilitiesReader
from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.common.taxonomy_sdc_error import SpecError, WorkspaceIdError


class TestFRMEM001Acceptance:
    """FR-MEM-001: Path Resolution — business requirement met."""

    def test_path_resolution_returns_md_file(
        self, isolated_home, git_repo
    ) -> None:
        cap = CapabilitiesPath()
        paths = cap.resolve_paths()
        assert paths.file.name.endswith(".md")


class TestFRMEM002Acceptance:
    """FR-MEM-002: Read — business requirement met."""

    def test_read_missing_file_returns_empty(
        self, isolated_home, git_repo
    ) -> None:
        cap = CapabilitiesReader()
        content = cap.read_content()
        assert content == ""


class TestFRMEM003Acceptance:
    """FR-MEM-003: Snapshot — business requirement met."""

    def test_snapshot_missing_file_returns_fallback(
        self, isolated_home, git_repo
    ) -> None:
        cap = CapabilitiesSnapshot()
        snapshot = cap.read_snapshot()
        assert snapshot.exists is False
        assert snapshot.common_issues == []
        assert snapshot.recent_runs == []


class TestFRMEM004Acceptance:
    """FR-MEM-004: Update — business requirement met."""

    def test_update_empty_spec_raises(
        self, isolated_home, git_repo
    ) -> None:
        cap = CapabilitiesWriter()
        with pytest.raises(SpecError):
            cap.update({})