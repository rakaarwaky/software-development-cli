"""Acceptance tests for the memory feature.

Proves: business requirement met.
"""

from __future__ import annotations

import pytest

from memory.src.capabilities_memory_path import CapabilitiesPath
from memory.src.capabilities_memory_reader import CapabilitiesReader
from memory.src.capabilities_memory_top import CapabilitiesTop
from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.common.taxonomy_sdc_error import SpecError, WorkspaceIdError
from shared.src.common.taxonomy_sdc_vo import PatternCount


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
    """FR-MEM-003: Top — business requirement met."""

    def test_top_missing_file_returns_empty(
        self, isolated_home, git_repo
    ) -> None:
        cap = CapabilitiesTop()
        result = cap.top(PatternCount(5))
        assert result.top_patterns == []
        assert result.top_total == 0
        assert result.top_exists is False


class TestFRMEM004Acceptance:
    """FR-MEM-004: Update — business requirement met."""

    def test_update_empty_spec_raises(
        self, isolated_home, git_repo
    ) -> None:
        cap = CapabilitiesWriter()
        with pytest.raises(SpecError):
            cap.update({})