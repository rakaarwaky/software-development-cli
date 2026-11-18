# BACKLOG — CLI Surface

## Progress Overview

The `sdc` surface is implemented: stdlib-only argument parsing with host, memory, plan, and helper-doc subcommands, exit codes 0/1/2/3/4, and capability injection from the root entry point.

## Backlog Status

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-CLI-001 | Done | `sdc host setup --subdir implement\|plan\|execute` (skill-name aliases `design`, `execute-plan` accepted) | P0 |
| BL-CLI-002 | Done | `sdc host cleanup <paths...>` (positional, missing paths skipped) | P0 |
| BL-CLI-003 | Done | `sdc memory path\|read\|snapshot\|update` | P0 |
| BL-CLI-004 | Done | `sdc validate-plan <plan-file>` | P1 |
| BL-CLI-005 | Done | Exit codes 0/1/2/3/4 with stderr messages | P0 |
| BL-CLI-006 | Done | Capabilities injected via `set_capabilities` from the root entry | P0 |

### FR-CLI-001: Subcommand Dispatch

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `cmd_sdc` parses argv and dispatches to host/memory/planner aggregates |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### FR-CLI-002: Host Subcommand

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `sdc host setup --subdir` and `sdc host cleanup` implemented |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### FR-CLI-003: Memory Subcommand

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `sdc memory path|read|snapshot|update` implemented |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### FR-CLI-004: Validate-Plan Subcommand

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `sdc validate-plan <plan-file>` implemented |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| ARCHITECTURE | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
| DESIGN       | Surface layer design contract              | [DESIGN.md](FRD.md) |
| FRD          | Functional requirements specification      | [FRD.md](FRD.md) |
| PRD          | Business goals, user stories, and scope    | [PRD.md](../../PRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |