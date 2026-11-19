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

from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
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


class TestCapabilitiesWriterWorkflow:
    """run.workflow provenance field: rendering, round-trip, validation."""

    def test_workflow_renders_before_rounds(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        res = writer.update(
            {
                "run": {
                    "workflow": "plan",
                    "description": "plan: retry-logic feature",
                    "rounds": 2,
                }
            }
        )
        text = Path(res.file).read_text(encoding="utf-8")
        assert "- **Workflow**: plan" in text
        assert text.index("**Workflow**") < text.index("**Rounds**")

    def test_workflow_round_trips_into_snapshot(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        writer.update({"run": {"workflow": "grill", "rounds": 3}})
        snapshot = CapabilitiesSnapshot().read_snapshot()
        runs = snapshot.recent_runs
        assert runs[0]["workflow"] == "grill"

    def test_run_without_workflow_yields_null_snapshot_field(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        writer.update({"run": {"rounds": 1}})
        snapshot = CapabilitiesSnapshot().read_snapshot()
        assert snapshot.recent_runs[0]["workflow"] is None

    def test_non_string_workflow_raises_spec_error(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        with pytest.raises(SpecError) as exc_info:
            writer.update({"run": {"workflow": 3}})
        assert exc_info.value.exit_code == 4
        assert '"run.workflow" must be a string' in str(exc_info.value)

    def test_empty_string_workflow_is_skipped(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        writer = CapabilitiesWriter()
        res = writer.update({"run": {"workflow": "  ", "rounds": 1}})
        text = Path(res.file).read_text(encoding="utf-8")
        assert "**Workflow**" not in text


def _concurrent_worker(spec: dict, home_dir: str, repo_dir: str) -> None:
    """Worker function for concurrency test running in separate process."""
    import os
    import sys
    from pathlib import Path

    os.environ["HOME"] = home_dir
    os.chdir(repo_dir)
    # The forkserver does not inherit the parent's sys.path mutations, so
    # re-bootstrap the module roots before importing memory.src.*.
    from shared.src.common.utility_sdc_common import bootstrap_ns_roots

    bootstrap_ns_roots()
    from memory.src.capabilities_memory_writer import CapabilitiesWriter

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
