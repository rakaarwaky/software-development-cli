"""Memory content reader capability (AES capabilities layer).

Implements IMemoryReaderProtocol: reads raw markdown content of the
memory file under ~/.agents/develop/<repo>/memory/.
"""

from __future__ import annotations

from shared.src.memory.contract_memory_protocol import IMemoryReaderProtocol
from shared.src.memory.utility_memory_helper import memory_paths

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesReader(IMemoryReaderProtocol):
    """Raw content reading capability."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def read_content(self) -> str:
        f = memory_paths()["file"]
        return f.read_text(encoding="utf-8") if f.exists() else ""

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create_default(cls) -> CapabilitiesReader:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesReader()"