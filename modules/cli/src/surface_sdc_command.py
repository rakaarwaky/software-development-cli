"""CLI surface — command handlers for the ``sdc`` verbs (AES surface layer).

Dispatches ``sdc <subcommand> [flags]`` to the host / memory / planner
capabilities via their contract aggregates. The surface is a thin
translator: argv becomes a request, the capability returns a typed
result, and the surface renders JSON to stdout.

Exit-code contract (primary agent-readable state signal):
  0  success
  1  classified runtime failure (host: not a git repo; memory: I/O error)
  2  usage error (unknown subcommand, missing required arg)
  3  memory lock timeout
  4  memory spec error (malformed JSON on stdin)
"""

from __future__ import annotations

import argparse
import json
import sys

from shared.src.common.taxonomy_sdc_error import (
    HostError,
    LockTimeoutError,
    MemoryHelperError,
    PlanUsageError,
    PlanValidationError,
    SdcError,
    SpecError,
    WorkspaceIdError,
)
from shared.src.host.taxonomy_host_request import HostRequest, HostResult
from shared.src.memory.taxonomy_memory_request import MemoryRequest, MemoryResult
from shared.src.planner.taxonomy_planner_request import PlanRequest, PlanResult


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sdc",
        description="Software Development CLI — consolidates implement/design/execute-plan helpers.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # sdc host <setup|cleanup>
    host = sub.add_parser("host", help="Host helpers (artifact root setup/cleanup).")
    host_sub = host.add_subparsers(dest="host_cmd", required=True)
    host_setup = host_sub.add_parser("setup", help="Create artifact root; print JSON {python, scratch_dir, run_id}.")
    host_setup.add_argument(
        "--subdir",
        required=True,
        choices=["implement", "plan", "execute"],
        help="Per-skill artifact subdir under ~/.agents/develop/<reponame>/.",
    )
    host_cleanup = host_sub.add_parser("cleanup", help="Unlink files; missing paths are ok.")
    host_cleanup.add_argument("paths", nargs="+", help="Files to unlink.")

    # sdc memory <path|read|snapshot|update>
    mem = sub.add_parser("memory", help="Workspace-scoped memory file manager.")
    mem_sub = mem.add_subparsers(dest="memory_cmd", required=True)
    mem_sub.add_parser("path", help="Print the memory file path for this workspace.")
    mem_sub.add_parser("read", help="Print the memory file contents (empty if missing).")
    mem_sub.add_parser("snapshot", help="Print the parsed memory file as JSON.")
    mem_update = mem_sub.add_parser(
        "update",
        help="Merge a JSON spec from stdin (or --file) into the memory file under an exclusive lock.",
    )
    mem_update.add_argument(
        "--file",
        help="Read the JSON spec from this path instead of stdin.",
    )

    # sdc validate-plan <design-doc-path>
    vp = sub.add_parser(
        "validate-plan",
        help="Validate the PR Plan DAG in a design document.",
    )
    vp.add_argument("path", help="Path to the design document.")

    return parser


def _dispatch_host(args: argparse.Namespace) -> int:
    if args.host_cmd == "setup":
        request = HostRequest(action="setup", subdir=args.subdir)
        result = _call_host(request)
        json.dump(
            {
                "python": result.python,
                "scratch_dir": result.scratch_dir,
                "run_id": result.run_id,
            },
            sys.stdout,
            separators=(",", ":"),
        )
        sys.stdout.write("\n")
        return 0
    if args.host_cmd == "cleanup":
        request = HostRequest(action="cleanup", paths=args.paths)
        result = _call_host(request)
        return 1 if result.failed_count else 0
    return 2


def _dispatch_memory(args: argparse.Namespace) -> int:
    if args.memory_cmd == "path":
        result = _call_memory(MemoryRequest(action="path"))
        print(result.path)
        return 0
    if args.memory_cmd == "read":
        result = _call_memory(MemoryRequest(action="read"))
        sys.stdout.write(result.content)
        return 0
    if args.memory_cmd == "snapshot":
        result = _call_memory(MemoryRequest(action="snapshot"))
        json.dump(result.snapshot, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.memory_cmd == "update":
        spec = _read_update_spec(args)
        result = _call_memory(MemoryRequest(action="update", spec=spec))
        json.dump(
            {
                "file": result.file,
                "existed_before": result.existed_before,
                "stats": result.stats,
                "total_categories": result.total_categories,
                "total_patterns": result.total_patterns,
                "total_recent_runs": result.total_recent_runs,
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 0
    return 2


def _dispatch_validate_plan(args: argparse.Namespace) -> int:
    request = PlanRequest(action="validate", path=args.path)
    result = _call_planner(request)
    json.dump(
        {
            "valid": result.valid,
            "pr_count": result.pr_count,
            "levels": result.levels,
            "max_parallelism": result.max_parallelism,
            "linearized_order": result.linearized_order,
            "level_assignments": result.level_assignments,
            "errors": result.errors,
        },
        sys.stdout,
        indent=2,
    )
    sys.stdout.write("\n")
    return 0 if result.valid else 1


def _read_update_spec(args: argparse.Namespace) -> dict:
    """Read the update JSON spec from ``--file`` or stdin."""
    if args.file:
        from pathlib import Path

        raw = Path(args.file).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    if not raw.strip():
        raise SpecError("update requires JSON spec on stdin or --file")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"invalid JSON on stdin: {exc}")
    if not isinstance(spec, dict):
        raise SpecError("update spec must be a JSON object")
    return spec


# ─── Capability dispatch (injected by root) ────────────────────────────

_HOST_CAPABILITY: object | None = None
_MEMORY_CAPABILITY: object | None = None
_PLANNER_CAPABILITY: object | None = None


def set_capabilities(
    host: object,
    memory: object,
    planner: object,
) -> None:
    """Inject the capability instances. Called by the root entry."""
    global _HOST_CAPABILITY, _MEMORY_CAPABILITY, _PLANNER_CAPABILITY
    _HOST_CAPABILITY = host
    _MEMORY_CAPABILITY = memory
    _PLANNER_CAPABILITY = planner


def _call_host(request: HostRequest) -> HostResult:
    if _HOST_CAPABILITY is None:
        raise HostError("host capability not wired; call set_capabilities first")
    return _HOST_CAPABILITY.execute(request)


def _call_memory(request: MemoryRequest) -> MemoryResult:
    if _MEMORY_CAPABILITY is None:
        raise MemoryHelperError("memory capability not wired; call set_capabilities first")
    return _MEMORY_CAPABILITY.execute(request)


def _call_planner(request: PlanRequest) -> PlanResult:
    if _PLANNER_CAPABILITY is None:
        raise PlanUsageError("planner capability not wired; call set_capabilities first")
    return _PLANNER_CAPABILITY.execute(request)


def cmd_sdc(argv: list[str]) -> int:
    """Entry point for ``sdc <subcommand> [flags]``.

    Parses argv, dispatches to the right capability via its contract
    aggregate, and returns the process exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.subcommand == "host":
            return _dispatch_host(args)
        if args.subcommand == "memory":
            return _dispatch_memory(args)
        if args.subcommand == "validate-plan":
            return _dispatch_validate_plan(args)
        return 2
    except (HostError, WorkspaceIdError, MemoryHelperError, PlanUsageError) as exc:
        print(f"sdc: {exc}", file=sys.stderr)
        return exc.exit_code
    except LockTimeoutError as exc:
        print(f"sdc: {exc}", file=sys.stderr)
        return exc.exit_code
    except SpecError as exc:
        print(f"sdc: {exc}", file=sys.stderr)
        return exc.exit_code
    except PlanValidationError as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
        return exc.exit_code
    except SdcError as exc:
        print(f"sdc: {exc}", file=sys.stderr)
        return exc.exit_code
    except OSError as exc:
        print(f"sdc: I/O error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(f"sdc: unexpected error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1