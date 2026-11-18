"""E2E tests for the memory feature.

Proves: full request lifecycle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory.src.agent_memory_orchestrator import AgentMemory
from memory.src.capabilities_memory_path import CapabilitiesPath
from memory.src.capabilities_memory_reader import CapabilitiesReader
from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
from memory.src.capabilities_memory_writer import CapabilitiesWriter
from shared.src.memory.taxonomy_memory_request import MemoryRequest


def _make_orchestrator() -> AgentMemory:
    return AgentMemory(
        path_cap=CapabilitiesPath(),
        reader_cap=CapabilitiesReader(),
        snapshot_cap=CapabilitiesSnapshot(),
        writer_cap=CapabilitiesWriter(),
    )


class TestMemoryE2E:
    """Full lifecycle: path → read → snapshot → update → read."""

    def test_path_read_snapshot_update_lifecycle(
        self, isolated_home: Path, git_repo: Path
    ) -> None:
        agent = _make_orchestrator()

        path_result = agent.execute(MemoryRequest(action="path"))
        assert path_result.path.endswith(".md")

        read_result = agent.execute(MemoryRequest(action="read"))
        assert isinstance(read_result.content, str)

        snap_result = agent.execute(MemoryRequest(action="snapshot"))
        assert isinstance(snap_result.snapshot, dict)
        assert "exists" in snap_result.snapshot

        update_result = agent.execute(
            MemoryRequest(
                action="update",
                spec={
                    "patterns": [
                        {
                            "category": "Error Handling",
                            "description": "missing try/except around file I/O",
                        }
                    ]
                },
            )
        )
        assert update_result.stats["new_patterns"] >= 0

        read_again = agent.execute(MemoryRequest(action="read"))
        assert "missing try/except" in read_again.content