"""Unit tests for CapabilitiesSnapshot (capabilities_memory_snapshot).

Covers:
- Missing file returns fallback payload {common_issues: [], recent_runs: [], exists: False}
- Existing file returns parsed payload with exists: True
- PermissionError propagates as OSError per FR-MEM-003
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
from shared.src.memory.utility_memory_helper import memory_paths


class TestCapabilitiesSnapshot:
    """Test snapshot parsing capability."""

    def test_missing_file_returns_fallback_payload(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        snapshot = CapabilitiesSnapshot()
        payload = snapshot.read_snapshot()

        assert payload.exists is False
        assert payload.common_issues == []
        assert payload.recent_runs == []

    def test_existing_file_returns_parsed_payload(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        paths = memory_paths(create_dir=True)
        file_path = paths["file"]
        content = (
            "# Agent Memory\n\n"
            "## Common Issues\n\n"
            "### Architecture\n"
            "- violated boundary (seen 2 times)\n\n"
            "## Recent Runs\n\n"
            "### 2026-11-18 — implement feature\n"
            "Run details here\n"
        )
        file_path.write_text(content, encoding="utf-8")

        snapshot = CapabilitiesSnapshot()
        payload = snapshot.read_snapshot()

        assert payload.exists is True
        assert len(payload.common_issues) == 1
        assert payload.common_issues[0]["category"] == "Architecture"
        assert payload.common_issues[0]["description"] == "violated boundary"
        assert payload.common_issues[0]["count"] == 2
        assert len(payload.recent_runs) == 1
        assert payload.recent_runs[0]["date"] == "2026-11-18"
        assert payload.recent_runs[0]["workflow"] is None

    def test_permission_error_propagates(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        paths = memory_paths(create_dir=True)
        file_path = paths["file"]
        file_path.write_text("content", encoding="utf-8")

        def mock_read_text(*args, **kwargs):
            raise PermissionError("Access denied")

        snapshot = CapabilitiesSnapshot()
        with patch.object(Path, "read_text", mock_read_text):
            with pytest.raises(PermissionError) as exc_info:
                snapshot.read_snapshot()

            assert "Access denied" in str(exc_info.value)
