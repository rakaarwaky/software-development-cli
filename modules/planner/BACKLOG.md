# BACKLOG — Planner Helper

## Progress Overview

The planner helper feature is implemented: PR-plan parsing and DAG validation (cycles, missing dependencies, level computation, linearisation).

## Backlog Status

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-PLAN-001 | Done | Per-repo plans under `plans/` from the host setup | P0 |
| BL-PLAN-002 | Done | PR-plan file parser (tasks, deps, acceptance criteria) | P0 |
| BL-PLAN-003 | Done | DAG validation: missing deps, duplicate IDs, cycles | P0 |
| BL-PLAN-004 | Done | Level computation + deterministic linearisation | P0 |
| BL-PLAN-005 | Done | Canonical block markers in capability implementation | P0 |

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