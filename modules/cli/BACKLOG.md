# BACKLOG — CLI Surface

## Progress Overview

The `sdc` surface is implemented: stdlib-only argument parsing with host, memory, plan, and helper-doc subcommands, exit codes 0/1/2/3/4, and capability injection from the root entry point.

## Backlog Status

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-CLI-001 | Done | `sdc host setup --subdir implement/design/execute-plan` | P0 |
| BL-CLI-002 | Done | `sdc host cleanup <paths...>` (positional, missing paths skipped) | P0 |
| BL-CLI-003 | Done | `sdc memory path|read|snapshot|update` (subdir omitted = host root) | P0 |
| BL-CLI-004 | Done | `sdc validate-plan <plan-file>` | P1 |
| BL-CLI-005 | Done | Exit codes 0/1/2/3/4 with stderr messages | P0 |
| BL-CLI-006 | Done | Capabilities injected via `set_capabilities` from the root entry | P0 |

## Reference

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [FRD.md](FRD.md)
- [PRD.md](../../PRD.md)
- [ROADMAP.md](../../ROADMAP.md)