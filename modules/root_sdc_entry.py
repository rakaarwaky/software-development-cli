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
_TOOLS_ROOT = _MODULES_ROOT.parent
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.append(str(_TOOLS_ROOT))

for _m in ("shared", "cli", "planner", "memory", "host"):
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
    """Construct the feature aggregates via their composition roots and
    inject them into the surface."""
    from cli.src.surface_sdc_command import set_capabilities
    from host.src.root_host_container import create_host_feature
    from memory.src.root_memory_container import create_memory_feature
    from planner.src.root_planner_container import create_planner_feature

    set_capabilities(
        host=create_host_feature(),
        memory=create_memory_feature(),
        planner=create_planner_feature(),
    )


def main(argv: list[str] | None = None) -> int:
    """Entry point for ``sdc <subcommand> [flags]``."""
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print(
            "Usage: sdc <host|memory|validate-plan> [flags]\n"
            "Run 'sdc --help' for details on available commands.",
            file=sys.stderr,
        )
        return 2
    _wire_capabilities()
    from cli.src.surface_sdc_command import cmd_sdc

    return cmd_sdc(args)


if __name__ == "__main__":
    raise SystemExit(main())