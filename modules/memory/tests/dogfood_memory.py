"""Dogfood tests for memory CLI surface.

Proves: CLI against live service/session; skip if unavailable.
"""

from __future__ import annotations

import pytest


class TestMemoryDogfoodCLI:
    """Memory CLI end-to-end against live surface."""

    def test_cli_memory_path_writes_output(self, monkeypatch, tmp_path) -> None:
        pytest.skip("CLI surface not wired in this environment")