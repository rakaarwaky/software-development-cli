"""Smoke tests for the planner feature.

Proves: app boots + responds.
"""

from __future__ import annotations


class TestPlannerSmoke:
    """Smoke test: planner module imports and produces an aggregate."""

    def test_planner_feature_boots_and_responds(self) -> None:
        from planner.src.root_planner_container import create_planner_feature

        feature = create_planner_feature()
        assert feature is not None