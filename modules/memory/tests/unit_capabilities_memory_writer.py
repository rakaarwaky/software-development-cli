"""Unit tests for CapabilitiesWriter (capabilities_memory_writer).

Covers:
- Spec validation: non-dict and falsy inputs raise SpecError(exit_code=4)
- Happy path: new patterns write memory file with existed_before=False
- Subsequent updates write with existed_before=True
- In-lock file existence check ordering and concurrency serialization
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path
from typing import Any

import pytest

from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.common.taxonomy_sdc_error import SpecError
from shared.src.memory.taxonomy_memory_request import MemoryResult


class TestCapabilitiesWriterValidation:
    """Test spec validation guards."""

    @pytest.mark.parametrize(
        "invalid_spec",
        [
            {},
            None,
            [],
            "",
            123,
            True,
            False,
            ["not", "a", "dict"],
        ],
    )
    def test_invalid_or_empty_spec_raises_spec_error(self, invalid_spec: Any) -> None:
        writer = CapabilitiesWriter()
        with pytest.raises(SpecError) as exc_info:
            writer.update(invalid_spec)

        assert exc_info.value.exit_code == 4
        assert "update requires a non-empty spec dict" in str(exc_info.value)


class TestCapabilitiesWriterLifecycle:
    """Test writing memory files and verifying existed_before transitions."""

    def test_first_write_existed_before_is_false(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        spec = {
            "patterns": [
                {
                    "category": "testing",
                    "description": "missing unit tests in memory module",
                }
            ]
        }
        res: MemoryResult = writer.update(spec)

        assert isinstance(res, MemoryResult)
        assert res.existed_before is False
        assert Path(res.file).exists()
        assert "missing unit tests in memory module" in Path(res.file).read_text(
            encoding="utf-8"
        )
        assert res.total_categories == 1
        assert res.total_patterns == 1

    def test_subsequent_write_existed_before_is_true(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        spec1 = {
            "patterns": [
                {
                    "category": "testing",
                    "description": "first pattern",
                }
            ]
        }
        res1 = writer.update(spec1)
        assert res1.existed_before is False

        spec2 = {
            "patterns": [
                {
                    "category": "testing",
                    "description": "second pattern",
                }
            ]
        }
        res2 = writer.update(spec2)
        assert res2.existed_before is True
        assert res2.total_patterns == 2


def _concurrent_worker(spec: dict, home_dir: str, repo_dir: str) -> None:
    """Worker function for concurrency test running in separate process."""
    import os
    from pathlib import Path
    from memory.src.capabilities_memory_writer import CapabilitiesWriter

    os.environ["HOME"] = home_dir
    os.chdir(repo_dir)
    writer = CapabilitiesWriter()
    writer.update(spec)


class TestCapabilitiesWriterConcurrency:
    """Test concurrency and exclusive flock serialization."""

    def test_concurrent_updates_serialize(
        self, isolated_home: Path, git_repo: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HOME", str(isolated_home))

        specs = [
            {
                "patterns": [
                    {
                        "category": f"category_{i}",
                        "description": f"concurrent pattern {i}",
                    }
                ]
            }
            for i in range(4)
        ]

        processes = [
            multiprocessing.Process(
                target=_concurrent_worker,
                args=(s, str(isolated_home), str(git_repo)),
            )
            for s in specs
        ]

        for p in processes:
            p.start()
        for p in processes:
            p.join(timeout=10)
            assert p.exitcode == 0

        writer = CapabilitiesWriter()
        check_spec = {
            "patterns": [
                {
                    "category": "final",
                    "description": "final check pattern",
                }
            ]
        }
        res = writer.update(check_spec)
        assert res.existed_before is True
        # All 4 categories from concurrent updates plus 1 final category should exist
        assert res.total_categories >= 5
