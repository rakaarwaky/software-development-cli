"""Unit tests for AgentMemory (agent_memory_orchestrator).

Covers:
- Routing path, read, snapshot, update actions to injected capabilities
- SpecError raised on unknown action
- Factory method AgentMemory.create()
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memory.src.agent_memory_orchestrator import AgentMemory
from shared.src.common.taxonomy_sdc_error import SpecError
from shared.src.common.taxonomy_sdc_vo import (
    PatternCategory,
    PatternCount,
    RepoPaths,
    WorkspaceId,
)
from shared.src.memory.taxonomy_memory_request import (
    MemoryRequest,
    MemoryResult,
)


class FakePathCap:
    def resolve_paths(self, *, create_dir: bool = False) -> RepoPaths:
        return RepoPaths(
            dir=Path("/tmp/memory"),
            file=Path("/tmp/memory/repo.md"),
            lock=Path("/tmp/memory/repo.lock"),
            workspace_id=WorkspaceId("test-repo-0123456789ab"),
        )


class FakeReaderCap:
    def __init__(self, content: str = "memory markdown content") -> None:
        self.content = content

    def read_content(self) -> str:
        return self.content


class FakeSnapshotCap:
    def __init__(self, snapshot: dict[str, Any] | None = None) -> None:
        self.snapshot = snapshot or {
            "common_issues": [],
            "recent_runs": [],
            "exists": True,
        }

    def read_snapshot(self) -> dict[str, Any]:
        return self.snapshot


class FakeWriterCap:
    def __init__(self) -> None:
        self.last_spec: dict | None = None

    def update(self, spec: dict) -> MemoryResult:
        self.last_spec = spec
        return MemoryResult(
            file="/tmp/memory/repo.md",
            existed_before=False,
            stats={"new_patterns": 1},
        )


class FakeTopCap:
    def __init__(self) -> None:
        self.last_call: tuple[PatternCount, PatternCategory | None] | None = None

    def top(
        self, n: PatternCount, category: PatternCategory | None = None
    ) -> MemoryResult:
        self.last_call = (n, category)
        return MemoryResult(
            top_patterns=[{"category": "Testing", "description": "x", "count": 2}],
            top_total=1,
            top_exists=True,
        )


@pytest.fixture()
def path_cap() -> FakePathCap:
    return FakePathCap()


@pytest.fixture()
def reader_cap() -> FakeReaderCap:
    return FakeReaderCap()


@pytest.fixture()
def snapshot_cap() -> FakeSnapshotCap:
    return FakeSnapshotCap()


@pytest.fixture()
def writer_cap() -> FakeWriterCap:
    return FakeWriterCap()


@pytest.fixture()
def top_cap() -> FakeTopCap:
    return FakeTopCap()


@pytest.fixture()
def agent(
    path_cap: FakePathCap,
    reader_cap: FakeReaderCap,
    snapshot_cap: FakeSnapshotCap,
    writer_cap: FakeWriterCap,
    top_cap: FakeTopCap,
) -> AgentMemory:
    return AgentMemory(
        path_cap=path_cap,
        reader_cap=reader_cap,
        snapshot_cap=snapshot_cap,
        writer_cap=writer_cap,
        top_cap=top_cap,
    )


class TestAgentMemoryDispatch:
    """Test routing to capabilities."""

    def test_dispatch_path_action(self, agent: AgentMemory) -> None:
        req = MemoryRequest(action="path")
        res = agent.execute(req)
        assert res.path == "/tmp/memory/repo.md"

    def test_dispatch_read_action(self, agent: AgentMemory) -> None:
        req = MemoryRequest(action="read")
        res = agent.execute(req)
        assert res.content == "memory markdown content"

    def test_dispatch_snapshot_action(self, agent: AgentMemory) -> None:
        req = MemoryRequest(action="snapshot")
        res = agent.execute(req)
        assert res.snapshot == {
            "common_issues": [],
            "recent_runs": [],
            "exists": True,
        }

    def test_dispatch_top_action(
        self, agent: AgentMemory, top_cap: FakeTopCap
    ) -> None:
        req = MemoryRequest(action="top", n=5, category="Testing")
        res = agent.execute(req)
        assert res.top_total == 1
        assert top_cap.last_call == (
            PatternCount(5),
            PatternCategory("Testing"),
        )

    def test_dispatch_top_empty_category_passes_none(
        self, agent: AgentMemory, top_cap: FakeTopCap
    ) -> None:
        req = MemoryRequest(action="top", n=10, category="")
        agent.execute(req)
        assert top_cap.last_call == (PatternCount(10), None)

    def test_dispatch_update_action(
        self, agent: AgentMemory, writer_cap: FakeWriterCap
    ) -> None:
        spec = {"patterns": [{"category": "code", "description": "lint"}]}
        req = MemoryRequest(action="update", spec=spec)
        res = agent.execute(req)
        assert res.file == "/tmp/memory/repo.md"
        assert res.stats == {"new_patterns": 1}
        assert writer_cap.last_spec.data == spec

    def test_unknown_action_raises_spec_error(self, agent: AgentMemory) -> None:
        req = MemoryRequest(action="invalid_action")
        with pytest.raises(SpecError) as exc_info:
            agent.execute(req)

        assert exc_info.value.exit_code == 4
        assert "memory: unknown action 'invalid_action'" in str(exc_info.value)
        assert "'path', 'read', 'snapshot', 'top', or 'update'" in str(exc_info.value)

    def test_create_factory(
        self,
        path_cap: FakePathCap,
        reader_cap: FakeReaderCap,
        snapshot_cap: FakeSnapshotCap,
        writer_cap: FakeWriterCap,
        top_cap: FakeTopCap,
    ) -> AgentMemory:
        ag = AgentMemory.create(
            path_cap=path_cap,
            reader_cap=reader_cap,
            snapshot_cap=snapshot_cap,
            writer_cap=writer_cap,
            top_cap=top_cap,
        )
        assert isinstance(ag, AgentMemory)
