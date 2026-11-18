"""Memory-domain request/response VOs (AES taxonomy layer)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MemoryRequest:
    """Request dispatched to the memory capability.

    ``action`` is one of ``path``, ``read``, ``snapshot``, ``update``.
    For ``update``, ``spec`` holds the parsed JSON dict (from stdin or
    ``--file``).
    """

    action: str
    spec: dict = field(default_factory=dict)
    file: str = ""


@dataclass(frozen=True)
class MemoryResult:
    """Result returned by the memory capability.

    For ``path``: ``path`` holds the memory file path.
    For ``read``: ``content`` holds the file contents (empty if missing).
    For ``snapshot``: ``snapshot`` holds the parsed JSON dict.
    For ``update``: ``file``, ``existed_before``, ``stats``, ``totals``.
    """

    path: str = ""
    content: str = ""
    snapshot: dict = field(default_factory=dict)
    file: str = ""
    existed_before: bool = False
    stats: dict = field(default_factory=dict)
    total_categories: int = 0
    total_patterns: int = 0
    total_recent_runs: int = 0