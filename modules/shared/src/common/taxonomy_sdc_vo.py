"""Shared-kernel value objects for the sdc domain (AES common taxonomy).

Pure-data VOs consumed by more than one module (host, planner, memory, cli).
Everything here is immutable data with no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

# ─── Host helper VOs ───────────────────────────────────────────────────

RepoSlug = NewType("RepoSlug", str)
"""Slugified repository name used as a directory component under the artifact root."""

SkillSubdir = NewType("SkillSubdir", str)
"""One of ``implement``, ``plan``, or ``execute`` — the per-skill artifact subdir."""

ArtifactRoot = NewType("ArtifactRoot", str)
"""Absolute path to ``~/.agents/develop/<reponame>/<subdir>/``."""

RunId = NewType("RunId", str)
"""Short (8-hex) unique identifier for one /implement or /planner run."""


@dataclass(frozen=True)
class HostSetup:
    """Payload returned by ``sdc host setup``."""

    python: str
    scratch_dir: str
    run_id: str


# ─── Memory VOs ────────────────────────────────────────────────────────

WorkspaceId = NewType("WorkspaceId", str)
"""``<readable-name>-<hash12>`` identifying one workspace (remote URL or path)."""

PatternDescription = NewType("PatternDescription", str)
"""One-line human-readable issue pattern description."""

PatternCategory = NewType("PatternCategory", str)
"""Category bucket name (e.g. ``Error Handling``, ``Other``)."""

PatternCount = NewType("PatternCount", int)
"""Number of times a pattern has been seen (increments on each dedup match)."""

MemoryContent = NewType("MemoryContent", str)
"""Raw markdown content of the memory file (empty string when missing)."""


@dataclass(frozen=True)
class RepoPaths:
    """Resolved filesystem paths for one repository's memory artifacts.

    ``dir`` is the memory directory, ``file`` the memory markdown file,
    ``lock`` the advisory-lock sibling, and ``workspace_id`` the derived
    workspace identifier.
    """

    dir: object
    file: object
    lock: object
    workspace_id: WorkspaceId


@dataclass(frozen=True)
class Pattern:
    """One recorded review pattern with its dedup count."""

    description: str
    count: int


@dataclass(frozen=True)
class RecentRun:
    """One logged /implement or /planner run summary entry."""

    date: str
    description: str
    body_lines: list[str]


# ─── Plan validator VOs ────────────────────────────────────────────────

PrId = NewType("PrId", str)
"""Lowercased ``pr-<n>`` identifier extracted from ``### PR N:`` headings."""


@dataclass(frozen=True)
class PrEntry:
    """One parsed PR entry from a design doc's PR Plan section."""

    id: str
    number: str
    title: str
    files: list[str]
    dependencies: list[str]
    description: str


@dataclass(frozen=True)
class PlanReport:
    """JSON-serialisable report returned by ``sdc validate-plan``."""

    valid: bool
    pr_count: int
    levels: int
    max_parallelism: int
    linearized_order: list[str]
    level_assignments: dict[str, int]
    errors: list[str]