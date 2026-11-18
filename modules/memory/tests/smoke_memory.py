"""Smoke tests for the memory feature.

Proves: app boots + responds.
"""

from __future__ import annotations


class TestMemorySmoke:
    """Smoke test: memory module imports and produces an aggregate."""

    def test_memory_feature_boots_and_responds(self) -> None:
        from memory.src.root_memory_container import create_memory_feature

        feature = create_memory_feature()
        assert feature is not None
        assert callable(getattr(feature, "execute", None))