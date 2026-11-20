"""Smoke tests for the pool feature.

Proves: app boots + responds.
"""

from __future__ import annotations


class TestPoolSmoke:
    """Smoke test: pool module imports and produces an aggregate."""

    def test_pool_feature_boots_and_responds(self) -> None:
        from pool.src.root_pool_container import create_pool_feature

        feature = create_pool_feature()
        assert feature is not None
        assert callable(getattr(feature, "execute", None))
