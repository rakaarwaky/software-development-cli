"""Tests for the CLI surface (``modules/cli/src/surface_sdc_command.py``).

Covers the exit-code contract (0/1/2/3/4), stderr-vs-stdout separation,
the unwired-capability error path, and capability injection/reset.

Bootstraps ``sys.path`` before any module imports so bare intra-module
imports resolve the same way as at CLI entry.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path

# ─── Bootstrap sys.path (mirrors modules/root_sdc_entry.py) ─────────────
_MODULES_ROOT = Path(__file__).resolve().parents[3]
for _m in ("shared", "cli", "planner", "memory"):
    _src = _MODULES_ROOT / _m / "src"
    if _src.is_dir():
        _p = str(_src)
        if _p not in sys.path:
            sys.path.insert(0, _p)
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from shared.src.common.utility_sdc_common import bootstrap_ns_roots

bootstrap_ns_roots()

from shared.src.common.taxonomy_sdc_error import (  # noqa: E402
    HostError,
    PlanUsageError,
    SdcError,
)
from shared.src.host.taxonomy_host_request import (  # noqa: E402
    HostRequest,
    HostResult,
)
from shared.src.memory.taxonomy_memory_request import (  # noqa: E402
    MemoryRequest,
    MemoryResult,
)
from shared.src.planner.taxonomy_planner_request import (  # noqa: E402
    PlanRequest,
    PlanResult,
)
from cli.src.surface_sdc_command import (  # noqa: E402
    cmd_sdc,
    reset_capabilities,
    set_capabilities,
)
from unittest.mock import MagicMock  # noqa: E402


def _wire(cap_host=None, cap_memory=None, cap_planner=None) -> None:
    """Wire fake capabilities into the surface, resetting first."""
    reset_capabilities()
    set_capabilities(
        host=cap_host or MagicMock(),
        memory=cap_memory or MagicMock(),
        planner=cap_planner or MagicMock(),
    )


class _Capture:
    """Capture stdout/stderr/exit_code from a ``cmd_sdc`` call."""

    def __init__(self) -> None:
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.code = 0

    def run(self, argv: list[str]) -> int:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = self.stdout, self.stderr
        try:
            self.code = cmd_sdc(argv)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return self.code


# ── host ────────────────────────────────────────────────────────────────

def test_host_setup_prints_json_and_exits_zero():
    cap = MagicMock()
    cap.dispatch.return_value = HostResult(
        python="/usr/bin/python3",
        scratch_dir="/tmp/scratch",
        run_id="abc12345",
    )
    _wire(cap_host=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["host", "setup", "--subdir", "implement"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 0
    data = json.loads(out.getvalue())
    assert data == {"python": "/usr/bin/python3", "scratch_dir": "/tmp/scratch", "run_id": "abc12345"}
    assert err.getvalue() == ""


def test_host_cleanup_partial_failure_exits_one():
    cap = MagicMock()
    cap.dispatch.return_value = HostResult(failed_count=2)
    _wire(cap_host=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["host", "cleanup", "/tmp/a", "/tmp/b"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1
    assert "could not be removed" in err.getvalue()
    assert out.getvalue() == ""


def test_host_cleanup_all_success_exits_zero():
    cap = MagicMock()
    cap.dispatch.return_value = HostResult(failed_count=0)
    _wire(cap_host=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["host", "cleanup", "/tmp/a"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 0


# ── memory ──────────────────────────────────────────────────────────────

def test_memory_path_prints_path():
    cap = MagicMock()
    cap.execute.return_value = MemoryResult(path="/home/raka/.agents/memory/sdc.json")
    _wire(cap_memory=cap)
    out = StringIO()
    old_out = sys.stdout
    sys.stdout = out
    try:
        code = cmd_sdc(["memory", "path"])
    finally:
        sys.stdout = old_out
    assert code == 0
    assert out.getvalue().strip() == "/home/raka/.agents/memory/sdc.json"


def test_memory_read_ends_with_newline():
    cap = MagicMock()
    cap.execute.return_value = MemoryResult(content="hello world")
    _wire(cap_memory=cap)
    out = StringIO()
    old_out = sys.stdout
    sys.stdout = out
    try:
        code = cmd_sdc(["memory", "read"])
    finally:
        sys.stdout = old_out
    assert code == 0
    assert out.getvalue() == "hello world\n"


def test_memory_read_empty_no_extra_newline():
    cap = MagicMock()
    cap.execute.return_value = MemoryResult(content="")
    _wire(cap_memory=cap)
    out = StringIO()
    old_out = sys.stdout
    sys.stdout = out
    try:
        code = cmd_sdc(["memory", "read"])
    finally:
        sys.stdout = old_out
    assert code == 0
    assert out.getvalue() == ""


def test_memory_snapshot_prints_json():
    cap = MagicMock()
    cap.execute.return_value = MemoryResult(snapshot={"cats": 1, "patterns": 2})
    _wire(cap_memory=cap)
    out = StringIO()
    old_out = sys.stdout
    sys.stdout = out
    try:
        code = cmd_sdc(["memory", "snapshot"])
    finally:
        sys.stdout = old_out
    assert code == 0
    assert json.loads(out.getvalue()) == {"cats": 1, "patterns": 2}


# ── validate-plan ───────────────────────────────────────────────────────

def test_validate_plan_valid_exits_zero():
    cap = MagicMock()
    cap.execute.return_value = PlanResult(valid=True, pr_count=2, errors=[])
    _wire(cap_planner=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["validate-plan", "design.md"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 0
    assert err.getvalue() == ""


def test_validate_plan_invalid_writes_stderr_exits_one():
    cap = MagicMock()
    cap.execute.return_value = PlanResult(valid=False, errors=["cycle: PR 1 -> PR 2"])
    _wire(cap_planner=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["validate-plan", "design.md"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1
    # The PlanResult (valid=False) is still rendered as JSON on stdout by
    # _dispatch_validate_plan — that is the result, not an error message.
    # The PlanValidationError path (stderr JSON) fires only when the
    # capability raises PlanValidationError directly.
    assert json.loads(out.getvalue())["valid"] is False


def test_validate_plan_raises_plan_validation_error():
    """When the planner raises PlanValidationError, output goes to stderr."""
    from shared.src.common.taxonomy_sdc_error import PlanValidationError

    cap = MagicMock()
    cap.execute.side_effect = PlanValidationError("DAG has a cycle: PR 1 -> PR 2")
    _wire(cap_planner=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["validate-plan", "design.md"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1
    assert out.getvalue() == ""
    data = json.loads(err.getvalue())
    assert data == {"valid": False, "errors": ["DAG has a cycle: PR 1 -> PR 2"]}


# ── error taxonomy ──────────────────────────────────────────────────────

def test_unwired_planner_exits_one_not_two():
    """Unwired planner is a runtime failure (exit 1), not a usage error (exit 2)."""
    reset_capabilities()
    set_capabilities(host=MagicMock(), memory=MagicMock(), planner=None)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["validate-plan", "design.md"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1, f"expected exit 1, got {code}"
    assert "planner capability not wired" in err.getvalue()


def test_unknown_subcommand_exits_two():
    import pytest

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        with pytest.raises(SystemExit) as exc_info:
            cmd_sdc(["bogus", "thing"])
        assert exc_info.value.code == 2
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def test_missing_required_arg_exits_two():
    import pytest

    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        with pytest.raises(SystemExit) as exc_info:
            cmd_sdc(["host", "setup"])
        assert exc_info.value.code == 2
    finally:
        sys.stdout, sys.stderr = old_out, old_err


# ── capability injection / reset ────────────────────────────────────────

def test_set_and_reset_capabilities_isolated():
    _wire()
    from cli.src.surface_sdc_command import _HOST_AGENT
    assert _HOST_AGENT is not None
    reset_capabilities()
    from cli.src.surface_sdc_command import _HOST_AGENT, _MEMORY_CAPABILITY, _PLANNER_CAPABILITY
    assert _HOST_AGENT is None
    assert _MEMORY_CAPABILITY is None
    assert _PLANNER_CAPABILITY is None


# ── unexpected error path ───────────────────────────────────────────────

def test_unexpected_error_prints_traceback_exits_one():
    cap = MagicMock()
    cap.dispatch.side_effect = TypeError("boom")
    _wire(cap_host=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["host", "setup", "--subdir", "implement"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1
    assert "TypeError" in err.getvalue()
    assert "boom" in err.getvalue()
    assert "Traceback" in err.getvalue()
