"""Planner-domain request/response VOs (AES taxonomy layer)."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.src.common.taxonomy_sdc_vo import PrEntry


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
    On failure: failures are surfaced as raised exceptions
    (``PlanParseError`` exit code 4, ``PlanValidationError`` exit code 1,
    ``PlanUsageError`` exit code 2). The ``errors`` field may carry
    non-fatal parse warnings collected alongside valid entries.
    """

    valid: bool = False
    pr_count: int = 0
    levels: int = 0
    max_parallelism: int = 0
    linearized_order: list[str] = field(default_factory=list)
    level_assignments: dict[str, int] = field(default_factory=dict)
    nodes: list[dict[str, object]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ─── Capability request/response VOs ───────────────────────────────────


@dataclass(frozen=True)
class PrEntryList:
    """A parsed list of PR entries from the PR Plan section."""

    text: str = ""
    entries: list[PrEntry] = field(default_factory=list)


@dataclass(frozen=True)
class ParseResult:
    """Result of parsing the PR Plan section."""

    ok: bool = False
    entries: list[PrEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ValidateResult:
    """Result of validating the PR dependency DAG."""

    ok: bool = False
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComputeResult:
    """Result of computing level assignments and linearization."""

    ok: bool = False
    levels: int = 0
    max_parallelism: int = 0
    linearized_order: list[str] = field(default_factory=list)
    level_assignments: dict[str, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)