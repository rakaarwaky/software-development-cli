# BACKLOG — Shared

## Progress Overview

The shared layer is implemented: taxonomy and contract (ABC) modules for host, memory, and planner, plus the sdc common utility (arg parsing, errors, paths, output).

## Backlog Status

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-SH-001 | Done | Taxonomy modules (host request/result, memory, planner) | P0 |
| BL-SH-002 | Done | Contracts as ABC + abstractmethod (protocol classes) | P0 |
| BL-SH-003 | Done | sdc common utility: parsing, errors, paths, output | P0 |
| BL-SH-004 | Done | Migrate skill helpers from `python3 scripts/*.py` to `sdc` subcommands | P0 |

### DT-HOST-001: Host Contracts

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `contract_host_aggregate.py` defines `IHostAggregate` ABC |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### DT-MEM-001: Memory Contracts

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `contract_memory_aggregate.py` defines `IMemoryAggregate` ABC |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### DT-PLAN-001: Planner Contracts

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `contract_planner_aggregate.py` defines `IPlanAggregate` ABC |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### DT-SDC-001: Taxonomy Constants

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `taxonomy_sdc_constant.py` provides artifact paths, memory config, naming patterns, exit codes |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### DT-SDC-002: Taxonomy Errors

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `taxonomy_sdc_error.py` defines `SdcError`, `WorkspaceIdError`, `LockTimeoutError`, `SpecError`, `MemoryHelperError`, `HostError`, `PlanValidationError`, `PlanUsageError` |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### DT-SDC-003: Taxonomy VOs

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `taxonomy_sdc_vo.py` defines `HostSetup`, `Pattern`, `RecentRun`, `PrEntry`, `PlanReport` |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### DT-SDC-004: Common Utilities

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `utility_sdc_common.py` provides `resolve_python`, `slugify`, `repo_slug`, `canonicalize_remote`, `sanitize_one_line`, `normalize`, `git_output` |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| DATA         | Shared data requirements specification     | [DATA.md](DATA.md) |
| ARCHITECTURE | System boundaries, tech stack, and infra   | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
| FRD          | Functional requirements specification      | [FRD.md](FRD.md) |
| PRD          | Business goals, user stories, and scope    | [PRD.md](../../PRD.md) |
| Roadmap      | Timeline, phasing, and dependencies        | [ROADMAP.md](../../ROADMAP.md) |