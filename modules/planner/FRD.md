# FRD — Plan Validator

## Feature Overview

The plan validator capability parses the `## PR Plan` section of a
design document, validates the PR dependency DAG, computes level
assignments, and linearises for final branch merge order.

## Functional Requirements

### FR-PLAN-001: Parse PR Plan

| Aspect | Detail |
|--------|--------|
| Input | design document markdown |
| Output | list of `PrEntry` dicts or parse errors |
| Protocol | `IPlanAggregate` |
| Method | `PlanValidator.execute(PlanRequest(action="validate", path=...))` |
| Event | none |
| Error | `PlanValidationError` if no PR Plan section or malformed entries |

### FR-PLAN-002: Validate DAG

| Aspect | Detail |
|--------|--------|
| Input | list of `PrEntry` |
| Output | list of error strings (empty if valid) |
| Protocol | `IPlanAggregate` |
| Method | `validate_dag(entries)` |
| Event | none |
| Error | Duplicate IDs, invalid references, cycle detected |

### FR-PLAN-003: Compute Execution Plan

| Aspect | Detail |
|--------|--------|
| Input | validated `PrEntry` list |
| Output | `{levels, max_parallelism, linearized_order, level_assignments}` |
| Protocol | `IPlanAggregate` |
| Method | `compute_levels()`, `linearize()` |
| Event | none |
| Error | none (only called on valid DAG) |

## Public Interface

### Protocol API

- `IPlanAggregate.execute(PlanRequest) → PlanResult`

### Aggregate API

- `PlanValidator` implements `IPlanAggregate`

## Reference

- [PRD.md](../../PRD.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](../../ROADMAP.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)