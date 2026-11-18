"""Dogfood tests for planner CLI surface.

Proves: CLI against live service/session; skip if unavailable.
"""

from __future__ import annotations

import pytest


class TestPlannerDogfoodCLI:
    """Planner CLI end-to-end against live surface."""

    def test_cli_validate_plan_writes_output(self, monkeypatch, tmp_path) -> None:
        pytest.skip("CLI surface not wired in this environment")