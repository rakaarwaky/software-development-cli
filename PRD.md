# PRD — software-development-cli

## Overview

`sdc` (software-development-cli) is a single binary that consolidates the
helper scripts used by the `software-development` skills (`implement`,
`design`, `execute-plan`) into one stdlib-only Python CLI. It replaces the
per-skill `scripts/host.py`, `scripts/memory.py`, and
`scripts/validate-plan.py` calls with a uniform `sdc <subcommand>` surface
so skill step files stay thin and consistent.

## Goals

1. **Single binary**: One `sdc` command with three subcommands (`host`,
   `memory`, `validate-plan`) replaces all per-skill helper scripts.
2. **Thin skill references**: Skill step files call `sdc ...` instead of
   `python3 .../scripts/host.py`.
3. **AES compliance**: The codebase follows the AES 7-layer architecture
   with contracts, capabilities, and surface layers.
4. **Stdlib-only**: No external dependencies beyond Python 3.9+ stdlib.

## Non-Goals

- MCP server (not needed; skills call `sdc` directly)
- Windows support (Linux-only, matching the original host.py constraint)
- Web UI or API server

## Success Metrics

- All three subcommands pass end-to-end tests against a real repo
- AES lint scan passes with no CRITICAL violations
- Skill references migrated from `python3 .../scripts/*.py` to `sdc ...`

## Reference

- [ROADMAP.md](ROADMAP.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)