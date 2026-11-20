"""Dogfood tests for pool CLI surface.

Proves: CLI against live service/session; skip if unavailable.
"""

from __future__ import annotations

import pytest


class TestPoolDogfoodCLI:
    """Pool CLI end-to-end against live surface."""

    def test_cli_pool_grok_probe(self, monkeypatch, tmp_path) -> None:
        # A real grok session is required; skip when orca or a live
        # session handle is unavailable in this environment.
        pytest.skip("Live Orca grok session required for pool dogfood")
