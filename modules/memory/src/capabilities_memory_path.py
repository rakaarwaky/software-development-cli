"""Memory path resolver capability (AES capabilities layer).

Implements IMemoryPathProtocol: resolves file and lock paths for the
active repository under ~/.agents/develop/<repo>/memory/.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.memory.contract_memory_protocol import IMemoryPathProtocol
from shared.src.memory.utility_memory_helper import memory_paths

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesPath(IMemoryPathProtocol):
    """Path resolution capability."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def resolve_paths(self, *, create_dir: bool = False) -> dict[str, Path]:
        return memory_paths(create_dir=create_dir)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create_default(cls) -> CapabilitiesPath:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesPath()"