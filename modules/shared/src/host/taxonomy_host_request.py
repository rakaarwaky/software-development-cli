"""Host-domain request/response VOs (AES taxonomy layer).

Pure-data VOs for the host helper contract. The CLI surface builds a
``HostRequest`` from argv; the capability returns a ``HostResult``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HostRequest:
    """Request dispatched to the host capability.

    ``action`` is one of ``setup`` or ``cleanup``.
    For ``setup``, ``subdir`` is one of ``implement``, ``plan``, ``execute``.
    For ``cleanup``, ``paths`` holds the file paths to unlink.
    """

    action: str
    subdir: str = ""
    paths: list[str] | None = None


@dataclass(frozen=True)
class HostResult:
    """Result returned by the host capability.

    For ``setup``: ``python``, ``scratch_dir``, ``run_id`` are populated.
    For ``cleanup``: ``failed_count`` holds the number of unlink failures.
    """

    python: str = ""
    scratch_dir: str = ""
    run_id: str = ""
    failed_count: int = 0