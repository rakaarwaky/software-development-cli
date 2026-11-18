"""Unit tests for CapabilitiesReader (capabilities_memory_reader).

Covers:
- Missing file returns empty string ""
- Existing file returns content verbatim
- PermissionError propagates as OSError per FR-MEM-002
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from memory.src.capabilities_memory_reader import CapabilitiesReader
from shared.src.memory.utility_memory_helper import memory_paths


class TestCapabilitiesReader:
    """Test reading memory file content."""

    def test_missing_file_returns_empty_string(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        reader = CapabilitiesReader()
        content = reader.read_content()
        assert content == ""

    def test_existing_file_returns_content_verbatim(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        paths = memory_paths(create_dir=True)
        file_path = paths["file"]
        expected_text = "# Test Memory\n\nSome saved patterns\n"
        file_path.write_text(expected_text, encoding="utf-8")

        reader = CapabilitiesReader()
        content = reader.read_content()
        assert content == expected_text

    def test_permission_error_propagates(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        paths = memory_paths(create_dir=True)
        file_path = paths["file"]
        file_path.write_text("protected content", encoding="utf-8")

        def mock_read_text(*args, **kwargs):
            raise PermissionError("Access denied")

        reader = CapabilitiesReader()
        with patch.object(Path, "read_text", mock_read_text):
            with pytest.raises(PermissionError) as exc_info:
                reader.read_content()

            assert "Access denied" in str(exc_info.value)
