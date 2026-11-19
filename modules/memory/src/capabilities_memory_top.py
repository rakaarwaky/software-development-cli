"""Memory top-patterns capability (AES capabilities layer).

Implements IMemoryTopProtocol: reads the memory file (read-only, no
lock — same posture as the reader capability) and returns
the top-N common issue patterns, optionally filtered by category.
"""

from __future__ import annotations

from shared.src.common.taxonomy_sdc_vo import (
    PatternCategory,
    PatternCount,
    WorkspaceId,
)
from shared.src.memory.contract_memory_protocol import IMemoryTopProtocol
from shared.src.memory.taxonomy_memory_request import MemoryResult
from shared.src.memory.utility_memory_helper import (
    get_workspace_id,
    memory_paths,
    parse_memory_file,
    top_patterns,
)

# ─── Block 1: Module Declaration ───────────────────────────────────────


class CapabilitiesTop(IMemoryTopProtocol):
    """Top-N common-issue pattern capability (read-only)."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def top(
        self, n: PatternCount, category: PatternCategory | None = None
    ) -> MemoryResult:
        _ = WorkspaceId(get_workspace_id())
        f = memory_paths()["file"]
        try:
            content = f.read_text(encoding="utf-8")
            exists = True
        except FileNotFoundError:
            content = ""
            exists = False
        state = parse_memory_file(content)
        patterns, total = top_patterns(state, n=n, category=category)
        return MemoryResult(
            top_patterns=patterns,
            top_total=total,
            top_exists=exists,
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @classmethod
    def create_default(cls) -> CapabilitiesTop:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesTop()"
