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
    """Instantiate the three capabilities and inject them into the surface."""
    from host.src.capabilities_host_implement import HostImplement
    from host.src.capabilities_host_design import HostDesign
    from host.src.capabilities_host_execute import HostExecute
    from memory.src.capabilities_memory_store import MemoryStore
    from planner.src.capabilities_plan_validator import PlanValidator
    from cli.src.surface_sdc_command import set_capabilities

    set_capabilities(
        host={
            "implement": HostImplement(),
            "design": HostDesign(),
            "execute": HostExecute(),
        },
        memory=MemoryStore(),
        planner=PlanValidator(),
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