"""Grok session polling capability (AES capabilities layer).

Implements ``IPoolGrokProtocol`` (poll): polls a Grok Build TUI session
running in an Orca terminal and detects completion. A full-screen TUI
agent renders to its terminal *screen*, not the PTY line stream, so
polling reads the screen with ``orca terminal read --screen --json`` and
paces with ``orca terminal wait --for tui-idle``. Completion is detected
from either the configured sentinel or a final-report shape (a PR marker
on a settled screen) — idle alone never means done, and a busy
(unsatisfied) wait is not an error.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable

from shared.src.common.taxonomy_sdc_error import PoolError
from shared.src.pool.contract_pool_protocol import IPoolGrokProtocol
from shared.src.pool.taxonomy_pool_constant import (
    FINAL_REPORT_PR_MARKERS,
    MAX_CONSECUTIVE_CLI_ERRORS,
    POOL_PAUSE_SECONDS,
    POOL_STATUS_DONE,
    POOL_STATUS_FAILED,
    POOL_STATUS_RUNNING,
    POOL_STATUS_UNKNOWN,
    SETTLED_PROMPT_MARKERS,
)
from shared.src.pool.taxonomy_pool_request import PoolRequest, PoolResult
from shared.src.pool.utility_pool_helper import (
    is_wait_satisfied,
    resolve_orca_cli,
    run_orca,
    screen_text,
    tail_lines,
    terminal_status,
)

# ─── Block 1: Module Declaration ──────────────────────────────────────


class CapabilitiesPoolGrok(IPoolGrokProtocol):
    """Polls Grok Build Orca terminal sessions (read-only; never sends).

    ``runner``, ``clock``, and ``sleeper`` are injectable for tests; the
    production wiring uses the real orca subprocess runner and the
    stdlib time functions.
    """

    def __init__(
        self,
        runner: Callable[[str, list[str]], dict] | None = None,
        clock: Callable[[], float] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._runner = runner if runner is not None else run_orca
        self._clock = clock if clock is not None else time.monotonic
        self._sleeper = sleeper if sleeper is not None else time.sleep

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def poll(self, request: PoolRequest) -> PoolResult:
        """Probe the session once, or block until completion or deadline."""
        orca = resolve_orca_cli(request.orca)
        start = self._clock()
        deadline = start + request.deadline_hours * 3600.0
        cli_errors = 0
        idle_cycles = 0
        cycles = 0
        while True:
            cycles += 1
            read_res = self._runner(orca, self._read_args(request))
            if not read_res:
                cli_errors += 1
                if cli_errors >= MAX_CONSECUTIVE_CLI_ERRORS:
                    self._note("ERROR: 10 consecutive CLI failures reading terminal")
                    raise PoolError(
                        f"pool: {MAX_CONSECUTIVE_CLI_ERRORS} consecutive orca CLI "
                        f"failures reading terminal {request.session_id!r}"
                    )
                self._note(
                    f"[{self._clock() - start:.0f}s] CLI failure "
                    f"{cli_errors}/{MAX_CONSECUTIVE_CLI_ERRORS} reading terminal"
                )
                self._sleeper(POOL_PAUSE_SECONDS)
                if not request.wait:
                    return self._result(
                        request,
                        POOL_STATUS_UNKNOWN,
                        cli_errors,
                        cycles,
                        start,
                        [],
                    )
                if self._clock() >= deadline:
                    return self._result(
                        request,
                        POOL_STATUS_RUNNING,
                        cli_errors,
                        cycles,
                        start,
                        [],
                        timed_out=True,
                    )
                continue
            cli_errors = 0

            text = screen_text(read_res)
            status = terminal_status(read_res)
            sentinel_hit = bool(request.sentinel) and request.sentinel in text
            report_hit = self._has_final_report(text)

            if sentinel_hit:
                self._note(f"SENTINEL: {request.sentinel}")
                return self._result(
                    request,
                    POOL_STATUS_DONE,
                    cli_errors,
                    cycles,
                    start,
                    tail_lines(text, request.tail),
                    sentinel=True,
                )

            if status == "exited":
                if report_hit:
                    self._note("DONE: terminal exited with final report on screen")
                    return self._result(
                        request,
                        POOL_STATUS_DONE,
                        cli_errors,
                        cycles,
                        start,
                        tail_lines(text, request.tail),
                        final_report=True,
                        terminal_status=status,
                    )
                self._note("ERROR: terminal exited without a final report — run failed")
                return self._result(
                    request,
                    POOL_STATUS_FAILED,
                    cli_errors,
                    cycles,
                    start,
                    tail_lines(text, request.tail),
                    final_report=False,
                    terminal_status=status,
                )

            if not request.wait:
                return self._result(
                    request,
                    POOL_STATUS_RUNNING,
                    cli_errors,
                    cycles,
                    start,
                    tail_lines(text, request.tail),
                    sentinel=False,
                    final_report=report_hit,
                    terminal_status=status,
                )

            wait_res = self._runner(orca, self._wait_args(request))
            satisfied = is_wait_satisfied(wait_res)
            if satisfied and report_hit:
                idle_cycles += 1
                self._note(
                    f"[{self._clock() - start:.0f}s] idle+report cycle "
                    f"{idle_cycles}/{request.idle_confirm}"
                )
                if idle_cycles >= request.idle_confirm:
                    self._note("DONE: final report detected on idle screen")
                    return self._result(
                        request,
                        POOL_STATUS_DONE,
                        cli_errors,
                        cycles,
                        start,
                        tail_lines(text, request.tail),
                        final_report=True,
                        terminal_status=status,
                    )
            else:
                # Either busy, or idle mid-turn without a report yet — keep polling.
                idle_cycles = 0
                state = "idle" if satisfied else "busy"
                self._note(
                    f"[{self._clock() - start:.0f}s] Grok {state} (no final report yet)"
                )

            self._sleeper(POOL_PAUSE_SECONDS)
            if self._clock() >= deadline:
                self._note("ERROR: polling deadline exceeded")
                return self._result(
                    request,
                    POOL_STATUS_RUNNING,
                    cli_errors,
                    cycles,
                    start,
                    tail_lines(text, request.tail),
                    timed_out=True,
                    terminal_status=status,
                )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    @staticmethod
    def _read_args(request: PoolRequest) -> list[str]:
        """Orca argv for a rendered-screen read of the session terminal."""
        return [
            "terminal",
            "read",
            "--terminal",
            request.session_id,
            "--screen",
            "--json",
        ]

    @staticmethod
    def _wait_args(request: PoolRequest) -> list[str]:
        """Orca argv for a paced tui-idle wait on the session terminal."""
        return [
            "terminal",
            "wait",
            "--terminal",
            request.session_id,
            "--for",
            "tui-idle",
            "--timeout-ms",
            str(request.wait_ms),
            "--json",
        ]

    @staticmethod
    def _has_final_report(text: str) -> bool:
        """Heuristic for a finished run's final-report block on the screen.

        A PR-shaped outcome marker plus a settled-prompt marker.
        """
        lowered = text.lower()
        has_pr = any(marker in lowered for marker in FINAL_REPORT_PR_MARKERS)
        settled = any(marker in lowered for marker in SETTLED_PROMPT_MARKERS)
        return has_pr and settled

    @staticmethod
    def _note(message: str) -> None:
        """Progress line to stderr so background notifies stay useful."""
        print(message, file=sys.stderr)

    def _result(
        self,
        request: PoolRequest,
        status: str,
        cli_errors: int,
        cycles: int,
        start: float,
        tail: list[str],
        sentinel: bool = False,
        final_report: bool = False,
        terminal_status: str = "",
        timed_out: bool = False,
    ) -> PoolResult:
        return PoolResult(
            session=request.session_id,
            status=status,
            sentinel=sentinel,
            final_report=final_report,
            terminal_status=terminal_status,
            timed_out=timed_out,
            cycles=cycles,
            cli_errors=cli_errors,
            tail=tail,
        )

    @classmethod
    def create_default(cls) -> CapabilitiesPoolGrok:
        return cls()

    def __repr__(self) -> str:
        return "CapabilitiesPoolGrok()"
