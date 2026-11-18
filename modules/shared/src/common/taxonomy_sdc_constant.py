"""Shared-kernel constants for the sdc domain (AES common layer).

Constants consumed by more than one module domain (cli, planner, memory).
A module imports from here rather than reaching into a sibling domain's
taxonomy.
"""

from __future__ import annotations

import re
from typing import Final

# ─── Artifact root ─────────────────────────────────────────────────────

#: Base directory under the user's home where per-repo artifact roots live.
DEVELOP_ROOT_DIRNAME: Final = ".agents"
DEVELOP_ROOT_SUBDIR: Final = "develop"

#: Per-skill artifact subdirectories under ``<develop_root>/<reponame>/``.
SKILL_SUBDIR_IMPLEMENT: Final = "implement"
SKILL_SUBDIR_PLAN: Final = "plan"
SKILL_SUBDIR_EXECUTE: Final = "execute"

# ─── Memory file ───────────────────────────────────────────────────────

#: Per-repo subdir under ``~/.agents/develop/<reponame>/`` that holds the
#: memory file and its lock sibling.
MEMORY_SUBDIR: Final = "memory"

#: Maximum patterns per category before compaction drops lowest-count entries.
MAX_PATTERNS_PER_CATEGORY: Final = 25

#: Maximum number of Recent Runs entries kept in the memory file.
MAX_RECENT_RUNS: Final = 20

#: Seconds to wait for an exclusive lock before raising LockTimeoutError.
LOCK_TIMEOUT_SECONDS: Final = 30

#: Poll interval (seconds) between lock acquisition attempts.
LOCK_POLL_INTERVAL: Final = 0.2

#: Timeout (seconds) for git subprocess calls during workspace id resolution.
GIT_TIMEOUT_SECONDS: Final = 5

#: File mode for memory and lock files (owner read/write only).
FILE_MODE: Final = 0o600

#: Canonical severities in fixed render order for run summaries.
SEVERITY_ORDER: Final = ("bug", "suggestion", "nit")

#: Default markdown header for a fresh memory file.
DEFAULT_HEADER: Final = [
    "# Implementation Review Patterns",
    "",
    "> This file is maintained by the /implement skill.",
    "> It records common issues found during implementation reviews to help avoid them in future runs.",
    "> Shared across all working directories that resolve to the same workspace id.",
]

# ─── Naming / slug ─────────────────────────────────────────────────────

#: Slug pattern: lowercase alphanumerics plus dashes, no leading/trailing/double dash.
_SLUG_DASH_RE: Final = re.compile(r"-{2,}")
_SLUG_INVALID_RE: Final = re.compile(r"[^a-z0-9-]+")

# ─── Canonical remote URL ──────────────────────────────────────────────

#: Hosts whose owner/repo path is case-insensitive.
CASE_INSENSITIVE_HOSTS: Final = frozenset(
    {"github.com", "gitlab.com", "bitbucket.org"}
)

#: Matches ``user@host:path`` (explicit SSH user).
SSH_REMOTE_RE: Final = re.compile(r"^[\w.-]+@([\w.-]+):(.+)$")

#: Matches bare ``host:path`` SSH shorthand (user supplied by ~/.ssh/config).
SSH_BARE_REMOTE_RE: Final = re.compile(r"^([\w-]+(?:\.[\w-]+)+):([^/].*)$")

#: Matches ``scheme://[user@]host[:port]/path`` URLs.
URL_REMOTE_RE: Final = re.compile(
    r"^[a-z][a-z0-9+.-]*://(?:[^@]+@)?([\w.-]+)(?::\d+)?(/.+)$",
    re.IGNORECASE,
)

# ─── Memory file markdown patterns ─────────────────────────────────────

SECTION_COMMON_ISSUES_RE: Final = re.compile(r"^##\s+Common Issues\s*$")
SECTION_RECENT_RUNS_RE: Final = re.compile(r"^##\s+Recent Runs\s*$")
CATEGORY_RE: Final = re.compile(r"^###\s+(.+?)\s*$")
ISSUE_RE: Final = re.compile(r"^-\s+(.+?)\s+\(seen\s+(\d+)\s+times?\)\s*$")
RUN_RE: Final = re.compile(
    r"^###\s+(\d{4}-\d{2}-\d{2})\s*[\u2014\u2013-]\s*(.+?)\s*$"
)
PUNCT_TAIL_RE: Final = re.compile(r"[.;:,!?\s]+$")
WHITESPACE_RE: Final = re.compile(r"\s+")

# ─── Exit codes ────────────────────────────────────────────────────────

EXIT_SUCCESS: Final = 0
EXIT_IO_ERROR: Final = 1
EXIT_WORKSPACE_ID: Final = 2
EXIT_LOCK_TIMEOUT: Final = 3
EXIT_SPEC_ERROR: Final = 4