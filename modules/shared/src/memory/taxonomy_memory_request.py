"""Memory-domain request/response VOs (AES taxonomy layer)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MemoryRequest:
    """Request dispatched to the memory capability.

    ``action`` is one of ``path``, ``read``, ``top``, ``update``.
    For ``update``, ``spec`` holds the parsed JSON dict (from
    stdin or ``--file``). For ``top``, ``n`` and ``category`` hold the
    top-N query parameters.
    """

    action: str
    spec: dict = field(default_factory=dict)
    file: str = ""
    n: int = 10
    category: str = ""


@dataclass(frozen=True)
class UpdateSpec:
    """A parsed JSON memory-update spec (patterns + optional run)."""

    data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryResult:
    """Result returned by the memory capability.

    For ``path``: ``path`` holds the memory file path.
    For ``read``: ``content`` holds the file contents (empty if missing).
    For ``top``: ``top_patterns`` holds the top-N ``{category,
    description, count}`` dicts, ``top_total`` the post-filter pattern
    count, and ``top_exists`` whether the memory file exists.
    For ``update``: ``file``, ``existed_before``, ``stats``, ``totals``.
    """

    path: str = ""
    content: str = ""
    file: str = ""
    existed_before: bool = False
    stats: dict = field(default_factory=dict)
    total_categories: int = 0
    total_patterns: int = 0
    total_recent_runs: int = 0
    top_patterns: list = field(default_factory=list)
    top_total: int = 0
    top_exists: bool = False