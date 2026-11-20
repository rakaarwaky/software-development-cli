"""Shared-kernel constants for the poll domain (AES taxonomy layer).

Policy constants for the agent-session poller: completion sentinels,
final-report heuristics, pacing limits, and default poll parameters.
Compile-time literals only (AES401).
"""

from __future__ import annotations

from typing import Final

# ─── Pool pacing ───────────────────────────────────────────────────────

#: Seconds between poll cycles in wait mode.
POOL_PAUSE_SECONDS: Final = 10

#: Per-cycle tui-idle wait timeout, in milliseconds.
DEFAULT_WAIT_MS: Final = 15000

#: Consecutive idle+final-report cycles required before declaring done.
DEFAULT_IDLE_CONFIRM: Final = 2

#: Default polling deadline in hours (wait mode).
DEFAULT_DEADLINE_HOURS: Final = 2

#: Subprocess timeout (seconds) for one orca CLI invocation.
ORCA_CLI_TIMEOUT_SECONDS: Final = 90

#: Consecutive genuine orca CLI/parse failures tolerated before aborting.
MAX_CONSECUTIVE_CLI_ERRORS: Final = 10

#: Number of trailing screen lines reported in the result tail.
DEFAULT_TAIL_LINES: Final = 50

# ─── Completion detection ──────────────────────────────────────────────

#: Default completion sentinel rendered on the agent's screen.
DEFAULT_POOL_SENTINEL: Final = "EXECUTE_PLAN_COMPLETE"

#: Markers that identify a finished run's final-report block (PR-shaped
#: outcome) on the rendered screen.
FINAL_REPORT_PR_MARKERS: Final = (
    "draft pr",
    "draft: #",
    "pr #",
    "pull request",
    "github.com/",
)

#: Markers that identify a settled prompt line after a finished run.
SETTLED_PROMPT_MARKERS: Final = (
    "worked for",
    "─ myomniroute",
    "always-approve",
)

# ─── Statuses and agents ───────────────────────────────────────────────

#: Session states reported by ``PoolResult.status``.
POOL_STATUS_DONE: Final = "done"
POOL_STATUS_FAILED: Final = "failed"
POOL_STATUS_RUNNING: Final = "running"
POOL_STATUS_UNKNOWN: Final = "unknown"

#: Agent kinds supported by the poller.
VALID_POOL_AGENTS: Final = ("grok",)
