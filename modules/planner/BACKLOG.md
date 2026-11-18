# BACKLOG — Planner Helper

## Progress Overview

The planner helper feature is implemented: PR-plan parsing and DAG validation (cycles, missing dependencies, level computation, linearisation).

## Backlog Status

### FR-PLAN-001: Parse PR Plan

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `capabilities_parse_pr_plan.py` extracts PR entries from the `## PR Plan` section |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### FR-PLAN-002: Validate DAG

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `capabilities_validate_dag.py` checks duplicate IDs, missing deps, and cycles |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### FR-PLAN-003: Compute Execution Plan

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `capabilities_compute_execution.py` computes levels, max parallelism, and merge order |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

## Reference

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [FRD.md](FRD.md)
- [PRD.md](../../PRD.md)
- [ROADMAP.md](../../ROADMAP.md)