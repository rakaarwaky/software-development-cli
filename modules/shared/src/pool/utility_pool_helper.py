"""Pool helper shared utility (AES utility layer).

Stateless mechanics for the agent-session poller: orca CLI resolution,
one-shot orca JSON invocation, and screen-text extraction from orca
read/wait responses. Lives in the shared kernel so the capability in
``modules/poll/src/`` stays thin (AES305).

No class definitions, no state — pure functions only (AES404).
"""

from __future__ import annotations

import json
import os
import shutil  # nosec: trusted system orca CLI lookup
import subprocess  # nosec: trusted system orca CLI calls

from shared.src.common.taxonomy_sdc_error import PoolError
from shared.src.pool.taxonomy_pool_constant import ORCA_CLI_TIMEOUT_SECONDS


def resolve_orca_cli(explicit: str = "") -> str:
    """Return the orca CLI executable to use.

    Precedence: an explicit ``explicit`` path, then ``ORCA_CLI_COMMAND``,
    then ``ORCA``, then ``orca-ide`` / ``orca`` on PATH. Raises
    ``PoolError`` when nothing resolves.
    """
    if explicit:
        return explicit
    for var in ("ORCA_CLI_COMMAND", "ORCA"):
        value = os.environ.get(var, "").strip()
        if value:
            return value
    for name in ("orca-ide", "orca"):
        found = shutil.which(name)
        if found:
            return found
    raise PoolError(
        "poll: no orca CLI found (set ORCA_CLI_COMMAND or pass --orca)"
    )


def run_orca(orca: str, args: list[str]) -> dict:
    """Run one orca CLI command and return its parsed JSON payload.

    Returns ``{}`` on any genuine CLI/parse failure (empty output,
    non-JSON stdout, timeout, or spawn error) — the caller classifies
    that as a CLI error, not a session state.
    """
    try:
        proc = subprocess.run(
            [orca, *args],
            capture_output=True,
            text=True,
            timeout=ORCA_CLI_TIMEOUT_SECONDS,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if not proc.stdout.strip():
        return {}
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def screen_text(read_res: dict) -> str:
    """Join the rendered screen lines of an orca terminal read response."""
    terminal = read_res.get("result", {}).get("terminal", {})
    return "\n".join(terminal.get("tail", []))


def tail_lines(text: str, n: int) -> list[str]:
    """Return the last ``n`` lines of ``text`` (empty list when empty)."""
    lines = text.splitlines()
    return lines[-n:] if n > 0 else []


def terminal_status(read_res: dict) -> str:
    """Return the orca terminal status (``running`` | ``exited`` | ``unknown``)."""
    terminal = read_res.get("result", {}).get("terminal", {})
    status = terminal.get("status", "")
    if status in ("running", "exited"):
        return status
    return "unknown"


def is_wait_satisfied(wait_res: dict) -> bool:
    """Return whether an orca ``terminal wait`` response was satisfied."""
    return bool(wait_res.get("result", {}).get("wait", {}).get("satisfied"))
