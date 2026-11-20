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

# ─── Bootstrap sys.path via the shared helper ──────────────────────────
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
from shared.src.pool.taxonomy_pool_request import (  # noqa: E402
    PoolRequest,
    PoolResult,
)
from cli.src.surface_sdc_command import (  # noqa: E402
    cmd_sdc,
    reset_capabilities,
    set_capabilities,
)
from unittest.mock import MagicMock  # noqa: E402


def _wire(cap_host=None, cap_memory=None, cap_planner=None, cap_pool=None) -> None:
    """Wire fake capabilities into the surface, resetting first."""
    reset_capabilities()
    set_capabilities(
        host=cap_host or MagicMock(),
        memory=cap_memory or MagicMock(),
        planner=cap_planner or MagicMock(),
        pool=cap_pool,
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
        code = cmd_sdc(["validate-plan", "plan.md"])
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
        code = cmd_sdc(["validate-plan", "plan.md"])
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
        code = cmd_sdc(["validate-plan", "plan.md"])
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
        code = cmd_sdc(["validate-plan", "plan.md"])
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

def test_unexpected_error_prints_error_exits_one():
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
    assert "boom" in err.getvalue()


# ── new behavior contracts ──────────────────────────────────────────────

def test_invalid_dag_report_goes_to_stdout_full_schema():
    """Invalid DAG → full 7-field JSON report on stdout, exit code 1."""
    from shared.src.common.taxonomy_sdc_error import PlanNotWiredError

    cap = MagicMock()
    cap.execute.return_value = PlanResult(
        valid=False,
        pr_count=2,
        levels=2,
        max_parallelism=1,
        linearized_order=["pr-1", "pr-2"],
        level_assignments={"pr-1": 0, "pr-2": 1},
        errors=["Cycle detected: pr-1 -> pr-2 -> pr-1"],
    )
    _wire(cap_planner=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["validate-plan", "plan.md"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1
    assert err.getvalue() == ""
    data = json.loads(out.getvalue())
    assert data["valid"] is False
    assert data["pr_count"] == 2
    assert data["levels"] == 2
    assert data["max_parallelism"] == 1
    assert data["errors"] == ["Cycle detected: pr-1 -> pr-2 -> pr-1"]


def test_bad_json_via_file_names_the_file_in_error():
    """--file with invalid JSON → 'invalid JSON in <file>', not 'on stdin'."""
    import tempfile, os

    bad_file = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    bad_file.write("{not valid json}")
    bad_file.close()
    try:
        out = StringIO()
        err = StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = cmd_sdc(["memory", "update", "--file", bad_file.name])
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        assert code == 4
        assert f"invalid JSON in {bad_file.name}" in err.getvalue()
        assert "stdin" not in err.getvalue()
    finally:
        os.unlink(bad_file.name)


def test_host_setup_accepts_skill_name_aliases():
    """--subdir planner → plan, --subdir execute-plan → execute."""
    cap = MagicMock()
    cap.dispatch.return_value = HostResult(
        python="/usr/bin/python3",
        scratch_dir="/tmp/scratch",
        run_id="abc12345",
    )
    _wire(cap_host=cap)
    for alias, canonical in [("planner", "plan"), ("execute-plan", "execute")]:
        out = StringIO()
        err = StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = cmd_sdc(["host", "setup", "--subdir", alias])
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        assert code == 0, alias
        args, _ = cap.dispatch.call_args
        assert args[0].subdir == canonical, alias


def test_host_setup_json_is_indented():
    """host setup output uses indented JSON (indent=2), matching other subcommands."""
    cap = MagicMock()
    cap.dispatch.return_value = HostResult(
        python="/usr/bin/python3",
        scratch_dir="/tmp/scratch",
        run_id="abc12345",
    )
    _wire(cap_host=cap)
    out = StringIO()
    old_out = sys.stdout
    sys.stdout = out
    try:
        code = cmd_sdc(["host", "setup", "--subdir", "implement"])
    finally:
        sys.stdout = old_out
    assert code == 0
    data = json.loads(out.getvalue())
    assert data == {"python": "/usr/bin/python3", "scratch_dir": "/tmp/scratch", "run_id": "abc12345"}
    # indent=2 produces multi-line output
    assert out.getvalue().count("\n") >= 2


# ── memory top ───────────────────────────────────────────────────────────

def _run_top(argv, result):
    cap = MagicMock()
    cap.execute.return_value = result
    _wire(cap_memory=cap)
    cap2 = MagicMock()
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, json.loads(out.getvalue()), err.getvalue(), cap


def test_memory_top_prints_json():
    res = MemoryResult(
        top_patterns=[{"category": "Testing", "description": "p", "count": 3}],
        top_total=7,
        top_exists=True,
    )
    code, data, err, cap = _run_top(["memory", "top"], res)
    assert code == 0
    assert data == {
        "patterns": [{"category": "Testing", "description": "p", "count": 3}],
        "total": 7,
        "exists": True,
    }
    assert err == ""
    req = cap.execute.call_args[0][0]
    assert req.action == "top"
    assert req.n == 10
    assert req.category == ""


def test_memory_top_n_and_category_flags():
    res = MemoryResult(top_patterns=[], top_total=0, top_exists=False)
    code, data, _, cap = _run_top(
        ["memory", "top", "--n", "5", "--category", "Planning"], res
    )
    assert code == 0
    req = cap.execute.call_args[0][0]
    assert req.n == 5
    assert req.category == "Planning"


def test_memory_top_invalid_n_exits_two():
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        try:
            cmd_sdc(["memory", "top", "--n", "0"])
            assert False, "expected SystemExit"
        except SystemExit as exc_info:
            assert exc_info.code == 2
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert "--n must be a positive integer" in err.getvalue()


# ── pool ───────────────────────────────────────────────────────────────


def _run_pool(argv: list[str], result: PoolResult) -> tuple[int, dict, str]:
    """Run a pool argv through the surface with a fake pool capability."""
    cap = MagicMock()
    cap.execute.return_value = result
    _wire(cap_pool=cap)
    out = StringIO()
    err = StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    data = json.loads(out.getvalue()) if out.getvalue().strip() else {}
    return code, data, err.getvalue()


def test_pool_grok_done_exits_zero():
    res = PoolResult(session="t1", status="done", sentinel=True, terminal_status="running")
    code, data, err = _run_pool(["pool", "grok", "t1"], res)
    assert code == 0
    assert data["session"] == "t1"
    assert data["status"] == "done"
    assert data["sentinel"] is True
    assert err == ""


def test_pool_grok_failed_exits_one():
    res = PoolResult(session="t1", status="failed", terminal_status="exited")
    code, data, _ = _run_pool(["pool", "grok", "t1"], res)
    assert code == 1
    assert data["status"] == "failed"
    assert data["final_report"] is False


def test_pool_grok_running_exits_zero():
    res = PoolResult(session="t1", status="running")
    code, data, _ = _run_pool(["pool", "grok", "t1"], res)
    assert code == 0
    assert data["status"] == "running"


def test_pool_grok_unknown_exits_one():
    res = PoolResult(session="t1", status="unknown")
    code, data, _ = _run_pool(["pool", "grok", "t1"], res)
    assert code == 1
    assert data["status"] == "unknown"


def test_pool_grok_timed_out_exits_three():
    res = PoolResult(session="t1", status="running", timed_out=True)
    code, data, _ = _run_pool(["pool", "grok", "--wait", "t1"], res)
    assert code == 3
    assert data["status"] == "running"
    assert data["timed_out"] is True


def test_pool_grok_forwards_flags():
    res = PoolResult(session="t1", status="running")
    cap = MagicMock()
    cap.execute.return_value = res
    _wire(cap_pool=cap)
    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(
            [
                "pool",
                "grok",
                "t1",
                "--wait",
                "--deadline-hours",
                "3",
                "--wait-ms",
                "5000",
                "--idle-confirm",
                "4",
                "--sentinel",
                "DONE",
                "--tail",
                "5",
                "--orca",
                "/bin/orca",
            ]
        )
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 0
    req = cap.execute.call_args[0][0]
    assert req.action == "poll"
    assert req.agent == "grok"
    assert req.session_id == "t1"
    assert req.wait is True
    assert req.deadline_hours == 3
    assert req.wait_ms == 5000
    assert req.idle_confirm == 4
    assert req.sentinel == "DONE"
    assert req.tail == 5
    assert req.orca == "/bin/orca"


def test_pool_missing_agent_is_usage_error():
    reset_capabilities()
    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        try:
            cmd_sdc(["pool"])
            assert False, "expected SystemExit"
        except SystemExit as exc_info:
            assert exc_info.code == 2
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def test_pool_grok_missing_session_id_is_usage_error():
    reset_capabilities()
    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        try:
            cmd_sdc(["pool", "grok"])
            assert False, "expected SystemExit"
        except SystemExit as exc_info:
            assert exc_info.code == 2
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def test_pool_not_wired_raises_pool_not_wired():
    reset_capabilities()
    # wire only host/memory/planner so pool stays None
    set_capabilities(host=MagicMock(), memory=MagicMock(), planner=MagicMock())
    out, err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = cmd_sdc(["pool", "grok", "t1"])
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    assert code == 1
    assert "pool agent not wired" in err.getvalue()
    reset_capabilities()

