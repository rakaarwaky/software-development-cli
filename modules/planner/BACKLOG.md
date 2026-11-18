# BACKLOG — Plan Validator

## Backlog

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-PLAN-001 | Done | Parse PR Plan section from design docs | P0 |
| BL-PLAN-002 | Done | DAG validation (unique IDs, valid refs, no cycles) | P0 |
| BL-PLAN-003 | Done | Level computation + linearization | P0 |
| BL-PLAN-004 | Done | JSON report output | P0 |
| BL-PLAN-005 | Todo | Support alternate PR heading formats | P2 |

## Done

- Ported from `scripts/validate-plan.py`
- Kahn's algorithm for cycle detection
- Numeric PR sorting (pr-2 before pr-10)
- Fenced code block stripping

## Next

- Support more heading formats
- Add cycle path visualization