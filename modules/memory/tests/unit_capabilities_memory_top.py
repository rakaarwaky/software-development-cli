"""Unit tests for CapabilitiesTop (capabilities_memory_top).

Covers:
- Missing memory file: exists=False, empty patterns, total 0
- Top-N slicing, count-desc ordering, and post-filter total
- Case/whitespace-insensitive category filter
- ``n < 1`` raises ``MemoryUsageError`` (UX-S5-003, UX-S5-004)
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory.src.capabilities_memory_top import CapabilitiesTop
from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.common.taxonomy_sdc_error import MemoryUsageError


@pytest.fixture()
def top_cap() -> CapabilitiesTop:
    return CapabilitiesTop()


class TestCapabilitiesTopMissing:
    """No memory file yet: empty result, exists False."""

    def test_missing_file_reports_empty(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        res = top_cap.top(10)
        assert res.top_exists is False
        assert res.top_patterns == []
        assert res.top_total == 0


class TestCapabilitiesTopSlicing:
    """Top-N ordering and slicing against a populated file."""

    @staticmethod
    def _seed(writer: CapabilitiesWriter, isolated_home: Path, git_repo: Path) -> None:
        # Counts: gamma 2, alpha 1, beta 1 (Testing); delta 3 (Security)
        writer.update(
            {
                "patterns": [
                    {"category": "Testing", "description": "alpha"},
                    {"category": "Testing", "description": "beta"},
                    {"category": "Testing", "description": "gamma"},
                ]
            }
        )
        writer.update(
            {
                "patterns": [
                    {"category": "Testing", "description": "gamma"},
                    {"category": "Security", "description": "delta"},
                    {"category": "Security", "description": "delta"},
                    {"category": "Security", "description": "delta"},
                ]
            }
        )

    def test_top_n_ordering_and_total(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        self._seed(CapabilitiesWriter(), isolated_home, git_repo)
        res = top_cap.top(2)
        assert res.top_exists is True
        assert res.top_total == 4
        assert [p["description"] for p in res.top_patterns] == ["delta", "gamma"]
        assert all(
            set(p) == {"category", "description", "count"} for p in res.top_patterns
        )
        assert res.top_patterns[0]["count"] == 3

    def test_top_larger_than_total_returns_all(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        self._seed(CapabilitiesWriter(), isolated_home, git_repo)
        res = top_cap.top(50)
        assert len(res.top_patterns) == 4
        assert res.top_total == 4
        # count-desc, then description-asc: delta(3), gamma(2), alpha(1), beta(1)
        assert [p["description"] for p in res.top_patterns] == [
            "delta",
            "gamma",
            "alpha",
            "beta",
        ]


class TestCapabilitiesTopCategoryFilter:
    """--category filter is case/whitespace-insensitive."""

    def test_category_filter_case_insensitive(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        TestCapabilitiesTopSlicing._seed(CapabilitiesWriter(), isolated_home, git_repo)
        res = top_cap.top(10, category="testing")
        assert res.top_total == 3
        assert all(p["category"] == "Testing" for p in res.top_patterns)
        assert [p["count"] for p in res.top_patterns] == [2, 1, 1]

    def test_unknown_category_yields_empty(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        TestCapabilitiesTopSlicing._seed(CapabilitiesWriter(), isolated_home, git_repo)
        res = top_cap.top(10, category="Nope")
        assert res.top_patterns == []
        assert res.top_total == 0
        assert res.top_exists is True


class TestCapabilitiesTopUsageErrors:
    """top must reject non-positive n with MemoryUsageError (exit_code=2)."""

    def test_top_n_zero_raises_memory_usage_error(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        with pytest.raises(MemoryUsageError) as exc_info:
            top_cap.top(0)
        assert exc_info.value.exit_code == 2

    def test_top_n_negative_raises_memory_usage_error(
        self, top_cap: CapabilitiesTop, isolated_home: Path, git_repo: Path
    ) -> None:
        with pytest.raises(MemoryUsageError) as exc_info:
            top_cap.top(-1)
        assert exc_info.value.exit_code == 2
