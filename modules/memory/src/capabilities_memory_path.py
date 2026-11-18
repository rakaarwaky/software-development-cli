"""Memory path resolver capability (AES capabilities layer).

Implements IMemoryPathProtocol: resolves file and lock paths for the
active repository under ~/.agents/develop/<repo>/memory/.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_vo import RepoPaths, WorkspaceId
from shared.src.memory.contract_memory_protocol import IMemoryPathProtocol
from shared.src.memory.utility_memory_helper import get_workspace_id, memory_paths

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesPath(IMemoryPathProtocol):
    """Path resolution capability."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def resolve_paths(self, *, create_dir: bool = False) -> RepoPaths:
        paths = memory_paths(create_dir=create_dir)
        workspace_id = WorkspaceId(get_workspace_id())
        return RepoPaths(
            dir=paths["dir"],
            file=paths["file"],
            lock=paths["lock"],
            workspace_id=workspace_id,
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create_default(cls) -> CapabilitiesPath:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesPath()"