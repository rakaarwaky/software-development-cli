"""Planner-domain request/response VOs (AES taxonomy layer)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlanRequest:
    """Request dispatched to the planner capability.

    ``action`` is one of ``validate``. For ``validate``, ``path`` holds
    the design document path.
    """

    action: str
    path: str = ""


@dataclass(frozen=True)
class PlanResult:
    """Result returned by the planner capability.

    On success: ``valid=True``, ``pr_count``, ``levels``,
    ``max_parallelism``, ``linearized_order``, ``level_assignments``.
    On failure: ``valid=False``, ``errors`` holds the error strings.
    """

    valid: bool = False
    pr_count: int = 0
    levels: int = 0
    max_parallelism: int = 0
    linearized_order: list[str] = field(default_factory=list)
    level_assignments: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)