"""Memory exclusive-lock writer capability (AES capabilities layer).

Implements IMemoryWriterProtocol: merges a run spec into the memory file
under exclusive flock, rendering the new markdown atomically.
"""

from __future__ import annotations

import os
from typing import Any

from shared.src.common.taxonomy_sdc_error import SpecError
from shared.src.memory.contract_memory_protocol import IMemoryWriterProtocol
from shared.src.memory.taxonomy_memory_request import MemoryResult, UpdateSpec
from shared.src.memory.utility_memory_helper import (
    acquire_lock,
    atomic_write,
    memory_paths,
    merge_run,
    parse_memory_file,
    release_lock,
    render_memory_file,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────

VALID_WORKFLOW_PREFIXES: tuple[str, ...] = ("impl: ", "exec: ", "plan: ", "grill: ")


class CapabilitiesWriter(IMemoryWriterProtocol):
    """Exclusive-lock update capability."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def update(self, spec: Any) -> MemoryResult:
        if isinstance(spec, dict):
            spec = UpdateSpec(data=spec)
        if not isinstance(spec, UpdateSpec) or not spec.data:
            raise SpecError("update requires a non-empty spec dict")

        # Validate run.workflow provenance before acquiring the lock / writing.
        run_spec = spec.data.get("run")
        if run_spec is not None and not isinstance(run_spec, dict):
            raise SpecError('"run" must be an object')
        self._validate_workflow(run_spec if isinstance(run_spec, dict) else None)

        paths = memory_paths(create_dir=True)
        file_path = paths["file"]
        lock_path = paths["lock"]

        fd = acquire_lock(lock_path)
        try:
            existed_before = file_path.exists()
            existing = file_path.read_text(encoding="utf-8") if existed_before else ""
            state = parse_memory_file(existing)
            stats = merge_run(state, spec.data)
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
            # Remove the lock file after releasing the flock. Safe: any
            # concurrent waiter that opened the file before unlinking still
            # holds a valid fd to the unlinked inode.
            try:
                os.unlink(str(lock_path))
            except OSError:
                pass

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @staticmethod
    def _validate_workflow(run_spec: dict | None) -> None:
        """Reject specs whose run.description lacks a recognized workflow prefix.

        If run_spec is None or empty, the update is patterns-only and is allowed.
        If run_spec has a description field, it must start with one of
        VALID_WORKFLOW_PREFIXES.
        """
        if not run_spec:
            return  # no run entry — allowed (patterns-only update)
        desc = run_spec.get("description")
        if desc is None:
            return  # run entry without description — allowed (e.g., workflow/rounds only)
        if not isinstance(desc, str):
            raise SpecError('"run.description" must be a string')
        if not any(desc.startswith(p) for p in VALID_WORKFLOW_PREFIXES):
            raise SpecError(
                f'"run.description" must start with one of {VALID_WORKFLOW_PREFIXES}; '
                f"got: {desc[:50]!r}"
            )

    @classmethod
    def create_default(cls) -> CapabilitiesWriter:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesWriter()"