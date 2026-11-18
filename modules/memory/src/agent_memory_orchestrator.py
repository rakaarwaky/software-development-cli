"""Memory agent orchestrator (AES agent layer).

Receives a MemoryRequest, routes to the owning protocol capability,
and returns a MemoryResult. No I/O, no computation — pure dispatch.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_error import SpecError
from shared.src.memory.contract_memory_aggregate import IMemoryAggregate
from shared.src.memory.contract_memory_protocol import (
    IMemoryPathProtocol,
    IMemoryReaderProtocol,
    IMemorySnapshotProtocol,
    IMemoryWriterProtocol,
)
from shared.src.memory.taxonomy_memory_request import MemoryRequest, MemoryResult

# ─── Block 1: Module Declaration ───────────────────────────────────────


class AgentMemory(IMemoryAggregate):
    """Agent orchestrator for the memory feature.

    Routes the 4 memory operations (path, read, snapshot, update) to
    their respective capability seams.
    """

    def __init__(
        self,
        path_cap: IMemoryPathProtocol,
        reader_cap: IMemoryReaderProtocol,
        snapshot_cap: IMemorySnapshotProtocol,
        writer_cap: IMemoryWriterProtocol,
    ) -> None:
        self._path = path_cap
        self._reader = reader_cap
        self._snapshot = snapshot_cap
        self._writer = writer_cap

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def execute(self, request: MemoryRequest) -> MemoryResult:
        if request.action == "path":
            return MemoryResult(path=str(self._path.resolve_paths()["file"]))
        if request.action == "read":
            return MemoryResult(content=self._reader.read_content())
        if request.action == "snapshot":
            return MemoryResult(snapshot=self._snapshot.read_snapshot())
        if request.action == "update":
            return self._writer.update(request.spec)
        raise SpecError(
            f"memory: unknown action {request.action!r}; "
            "expected 'path', 'read', 'snapshot', or 'update'"
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create(
        cls,
        path_cap: IMemoryPathProtocol,
        reader_cap: IMemoryReaderProtocol,
        snapshot_cap: IMemorySnapshotProtocol,
        writer_cap: IMemoryWriterProtocol,
    ) -> AgentMemory:
        return cls(
            path_cap=path_cap,
            reader_cap=reader_cap,
            snapshot_cap=snapshot_cap,
            writer_cap=writer_cap,
        )

    def __repr__(self) -> str:
        return "AgentMemory()"