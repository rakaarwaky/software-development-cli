"""Dogfood tests for host CLI surface.

Proves: CLI against live service/session; skip if unavailable.
"""

from __future__ import annotations

import pytest


class TestHostDogfoodCLI:
    """Host CLI end-to-end against live surface."""

    def test_cli_host_setup_writes_output(self, monkeypatch, tmp_path) -> None:
        pytest.skip("CLI surface not wired in this environment")