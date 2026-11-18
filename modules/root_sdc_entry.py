"""sdc CLI entry (AES root layer).

Single entry point for ``sdc <subcommand> [flags]``. Parses argv, wires
the capabilities into the surface via ``set_capabilities``, and returns
the process exit code.
"""

from __future__ import annotations

import sys
from pathlib import Path

_MODULES_ROOT = Path(__file__).resolve().parent

# Bootstrap sys.path so bare intra-module imports resolve.
for _m in ("shared", "cli", "planner", "memory"):
    _src = _MODULES_ROOT / _m / "src"
    if _src.is_dir():
        _p = str(_src)
        if _p not in sys.path:
            sys.path.append(_p)
if str(_MODULES_ROOT) not in sys.path:
    sys.path.append(str(_MODULES_ROOT))

from shared.src.common.utility_sdc_common import bootstrap_ns_roots

bootstrap_ns_roots()


def _wire_capabilities() -> None:
    """Instantiate the capabilities and inject them into the surface."""
    from host.src.agent_host_orchestrator import HostAgent
    from memory.src.capabilities_memory_path import CapabilitiesPath
    from memory.src.capabilities_memory_reader import CapabilitiesReader
    from memory.src.capabilities_memory_snapshot import CapabilitiesSnapshot
    from memory.src.capabilities_memory_writer import CapabilitiesWriter
    from memory.src.agent_memory_orchestrator import AgentMemory
    from planner.src.agent_planner_orchestrator import AgentPlanner
    from planner.src.capabilities_parse_pr_plan import CapabilitiesParsePrPlan
    from planner.src.capabilities_validate_dag import CapabilitiesValidateDag
    from planner.src.capabilities_compute_execution import CapabilitiesComputeExecution
    from cli.src.surface_sdc_command import set_capabilities

    parser = CapabilitiesParsePrPlan()
    validator = CapabilitiesValidateDag()
    computer = CapabilitiesComputeExecution()

    set_capabilities(
        host=HostAgent(),
        memory=AgentMemory(
            path_cap=CapabilitiesPath(),
            reader_cap=CapabilitiesReader(),
            snapshot_cap=CapabilitiesSnapshot(),
            writer_cap=CapabilitiesWriter(),
        ),
        planner=AgentPlanner(
            parser=parser,
            validator=validator,
            computer=computer,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``sdc <subcommand> [flags]``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "Usage: sdc <host|memory|validate-plan> [flags]",
            file=sys.stderr,
        )
        return 2
    _wire_capabilities()
    from cli.src.surface_sdc_command import cmd_sdc

    return cmd_sdc(args)


if __name__ == "__main__":
    raise SystemExit(main())