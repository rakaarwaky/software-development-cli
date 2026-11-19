"""Memory agent orchestrator (AES agent layer).

Receives a MemoryRequest, routes to the owning protocol capability,
and returns a MemoryResult. No I/O, no computation — pure dispatch.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_error import SpecError
from shared.src.common.taxonomy_sdc_vo import PatternCategory, PatternCount
from shared.src.memory.contract_memory_aggregate import IMemoryAggregate
from shared.src.memory.contract_memory_protocol import (
    IMemoryPathProtocol,
    IMemoryReaderProtocol,
    IMemorySnapshotProtocol,
    IMemoryTopProtocol,
    IMemoryWriterProtocol,
)
from shared.src.memory.taxonomy_memory_request import (
    MemoryRequest,
    MemoryResult,
    MemorySnapshot,
    UpdateSpec,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────


class AgentMemory(IMemoryAggregate):
    """Agent orchestrator for the memory feature.

    Routes the 5 memory operations (path, read, snapshot, top, update)
    to their respective capability seams.
    """

    def __init__(
        self,
        path_cap: IMemoryPathProtocol,
        reader_cap: IMemoryReaderProtocol,
        snapshot_cap: IMemorySnapshotProtocol,
        writer_cap: IMemoryWriterProtocol,
        top_cap: IMemoryTopProtocol,
    ) -> None:
        self._path = path_cap
        self._reader = reader_cap
        self._snapshot = snapshot_cap
        self._writer = writer_cap
        self._top = top_cap

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def execute(self, request: MemoryRequest) -> MemoryResult:
        if request.action == "path":
            paths = self._path.resolve_paths()
            return MemoryResult(path=str(paths.file))
        if request.action == "read":
            return MemoryResult(content=str(self._reader.read_content()))
        if request.action == "snapshot":
            return MemoryResult(snapshot=self._snapshot_payload())
        if request.action == "top":
            n = PatternCount(request.n)
            category = PatternCategory(request.category) if request.category else None
            return self._top.top(n, category)
        if request.action == "update":
            return self._writer.update(self._as_update_spec(request.spec))
        raise SpecError(
            f"memory: unknown action {request.action!r}; "
            "expected 'path', 'read', 'snapshot', 'top', or 'update'"
        )

    def _snapshot_payload(self) -> dict:
        """Return the snapshot as a plain dict for JSON rendering."""
        snapshot = self._snapshot.read_snapshot()
        return _snapshot_to_dict(snapshot)

    @staticmethod
    def _as_update_spec(spec: object) -> UpdateSpec:
        """Coerce a raw dict into an ``UpdateSpec``."""
        if isinstance(spec, UpdateSpec):
            return spec
        if isinstance(spec, dict):
            return UpdateSpec(data=spec)
        raise SpecError("update spec must be an UpdateSpec or a dict")

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create(
        cls,
        path_cap: IMemoryPathProtocol,
        reader_cap: IMemoryReaderProtocol,
        snapshot_cap: IMemorySnapshotProtocol,
        writer_cap: IMemoryWriterProtocol,
        top_cap: IMemoryTopProtocol,
    ) -> AgentMemory:
        return cls(
            path_cap=path_cap,
            reader_cap=reader_cap,
            snapshot_cap=snapshot_cap,
            writer_cap=writer_cap,
            top_cap=top_cap,
        )

    def __repr__(self) -> str:
        return "AgentMemory()"


def _snapshot_to_dict(snapshot: object) -> dict:
    """Coerce a ``MemorySnapshot`` VO into a plain dict for JSON rendering."""
    if isinstance(snapshot, dict):
        return snapshot
    if isinstance(snapshot, MemorySnapshot):
        return {
            "common_issues": list(snapshot.common_issues),
            "recent_runs": list(snapshot.recent_runs),
            "exists": snapshot.exists,
        }
    raise SpecError("snapshot must be a MemorySnapshot or a dict")