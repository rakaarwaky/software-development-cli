"""Memory exclusive-lock writer capability (AES capabilities layer).

Implements IMemoryWriterProtocol: merges a run spec into the memory file
under exclusive flock, rendering the new markdown atomically.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.memory.contract_memory_protocol import IMemoryWriterProtocol
from shared.src.memory.taxonomy_memory_request import MemoryResult
from shared.src.memory.utility_memory_helper import (
    acquire_lock,
    atomic_write,
    merge_run,
    memory_paths,
    parse_memory_file,
    release_lock,
    render_memory_file,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesWriter(IMemoryWriterProtocol):
    """Exclusive-lock update capability."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def update(self, spec: dict) -> MemoryResult:
        if not spec:
            raise ValueError("update requires a non-empty spec dict")

        paths = memory_paths(create_dir=True)
        file_path = paths["file"]
        lock_path = paths["lock"]

        existed_before = file_path.exists()
        fd = acquire_lock(lock_path)
        try:
            existing = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
            state = parse_memory_file(existing)
            stats = merge_run(state, spec)
            new_content = render_memory_file(state)
            atomic_write(file_path, new_content)

            return MemoryResult(
                file=str(file_path),
                existed_before=existed_before,
                stats=stats,
                total_categories=len(
                    [c for c, e in state["common_issues"].items() if e]
                ),
                total_patterns=sum(
                    len(e) for e in state["common_issues"].values()
                ),
                total_recent_runs=len(state["recent_runs"]),
            )
        finally:
            release_lock(fd)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create_default(cls) -> "CapabilitiesWriter":
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesWriter()"