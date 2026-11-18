"""Shared-kernel error types for the sdc domain (AES common taxonomy).

Every sdc subcommand raises a subclass of ``SdcError`` for classified
failures. The CLI surface catches these, prints ``sdc <sub>: <msg>`` to
stderr, and exits with the subclass's ``exit_code`` so the agent gets a
stable machine-readable signal.
"""

from __future__ import annotations


class SdcError(Exception):
    """Base exception type for the sdc module."""

    exit_code: int = 1


class WorkspaceIdError(SdcError):
    """Raised when no usable workspace id can be derived."""

    exit_code = 2


class LockTimeoutError(SdcError):
    """Raised when an exclusive lock can't be acquired within the deadline."""

    exit_code = 3


class SpecError(SdcError):
    """Raised when stdin JSON is missing, malformed, or fails validation."""

    exit_code = 4


class MemoryHelperError(SdcError):
    """Raised when the memory helper can't open its lock file or classify an I/O error."""

    exit_code = 1


class HostError(SdcError):
    """Raised when the host helper can't resolve the artifact root."""

    exit_code = 1


class PlanValidationError(SdcError):
    """Raised when the PR Plan DAG is invalid or the document is malformed."""

    exit_code = 1


class PlanUsageError(SdcError):
    """Raised when validate-plan receives a bad argv or unreadable file."""

    exit_code = 2