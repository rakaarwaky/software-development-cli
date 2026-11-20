"""Pool-domain request/response VOs (AES taxonomy layer).

Pure-data VOs for the agent-session poller contract. The CLI surface
builds a ``PoolRequest`` from argv; the capability returns a
``PoolResult``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.src.pool.taxonomy_pool_constant import (
    DEFAULT_DEADLINE_HOURS,
    DEFAULT_IDLE_CONFIRM,
    DEFAULT_POOL_SENTINEL,
    DEFAULT_TAIL_LINES,
    DEFAULT_WAIT_MS,
)


@dataclass(frozen=True)
class PoolRequest:
    """Request dispatched to the poll capability.

    ``action`` is ``poll``. ``agent`` is the agent kind whose session is
    being polled (``grok`` today). ``session_id`` is the Orca terminal
    handle that owns the running session.

    Pacing knobs (``wait``, ``deadline_hours``, ``wait_ms``,
    ``idle_confirm``) shape the wait loop; ``sentinel`` overrides the
    completion sentinel; ``tail`` sizes the result screen tail; ``orca``
    overrides the orca CLI executable.
    """

    action: str = "poll"
    agent: str = "grok"
    session_id: str = ""
    wait: bool = False
    deadline_hours: int = DEFAULT_DEADLINE_HOURS
    wait_ms: int = DEFAULT_WAIT_MS
    idle_confirm: int = DEFAULT_IDLE_CONFIRM
    sentinel: str = DEFAULT_POOL_SENTINEL
    tail: int = DEFAULT_TAIL_LINES
    orca: str = ""


@dataclass(frozen=True)
class PoolResult:
    """Result returned by the poll capability.

    ``status`` is one of ``done``, ``failed``, ``running``, ``unknown``:
    - ``done``: completion detected (sentinel on screen, or terminal
      exited / idle with a final report on screen).
    - ``failed``: terminal exited without a final report — the run failed.
    - ``running``: session still active (single probe, or a wait that
      hit its deadline; see ``timed_out``).
    - ``unknown``: the orca CLI could not be read (single probe).

    ``sentinel``/``final_report`` record which completion heuristic fired;
    ``terminal_status`` is the orca terminal status
    (``running`` | ``exited`` | ``unknown``); ``tail`` holds the last
    ``N`` rendered screen lines.
    """

    session: str = ""
    status: str = ""
    sentinel: bool = False
    final_report: bool = False
    terminal_status: str = ""
    timed_out: bool = False
    cycles: int = 0
    cli_errors: int = 0
    tail: list[str] = field(default_factory=list)
