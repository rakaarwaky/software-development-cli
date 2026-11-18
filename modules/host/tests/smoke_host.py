"""Smoke tests for the host feature.

Proves: app boots + responds.
"""

from __future__ import annotations


class TestHostSmoke:
    """Smoke test: host module imports and produces an aggregate."""

    def test_host_feature_boots_and_responds(self) -> None:
        from host.src.root_host_container import create_host_feature

        feature = create_host_feature()
        assert feature is not None
        assert callable(getattr(feature, "dispatch", None))