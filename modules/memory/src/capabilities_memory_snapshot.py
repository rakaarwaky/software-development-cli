"""Memory snapshot parser capability (AES capabilities layer).

Implements IMemorySnapshotProtocol: parses markdown into structured
JSON snapshot {common_issues, recent_runs, exists}.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_vo import WorkspaceId
from shared.src.memory.contract_memory_protocol import IMemorySnapshotProtocol
from shared.src.memory.utility_memory_helper import (
    build_snapshot_payload,
    get_workspace_id,
    memory_paths,
    parse_memory_file,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────

_EMPTY_STATE: dict[str, object] = {
    "header": [],
    "common_issues": {},
    "recent_runs": [],
}


class CapabilitiesSnapshot(IMemorySnapshotProtocol):
    """Structured parsing capability."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def read_snapshot(self) -> dict[str, object]:
        _ = WorkspaceId(get_workspace_id())
        f = memory_paths()["file"]
        try:
            state = parse_memory_file(f.read_text(encoding="utf-8"))
            payload = build_snapshot_payload(state, exists=True)
        except FileNotFoundError:
            payload = build_snapshot_payload(
                _EMPTY_STATE,
                exists=False,
            )
        return payload

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create_default(cls) -> CapabilitiesSnapshot:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesSnapshot()"