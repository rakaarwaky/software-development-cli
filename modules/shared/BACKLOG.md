# BACKLOG — Shared Kernel

## Backlog

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-SHARED-001 | Done | Taxonomy constants (paths, memory config, naming) | P0 |
| BL-SHARED-002 | Done | Taxonomy errors (SdcError hierarchy) | P0 |
| BL-SHARED-003 | Done | Taxonomy VOs (HostSetup, Pattern, PrEntry, PlanReport) | P0 |
| BL-SHARED-004 | Done | Common utilities (slugify, canonicalize, normalize) | P0 |
| BL-SHARED-005 | Done | Host contract (IHostAggregate) | P0 |
| BL-SHARED-006 | Done | Memory contract (IMemoryAggregate) | P0 |
| BL-SHARED-007 | Done | Planner contract (IPlanAggregate) | P0 |

## Done

- Shared kernel established with taxonomy + contract + utility layers
- All contracts follow AES402 (ABC with abstractmethod)
- All taxonomy files follow AES401 (pure data, no I/O)

## Next

- None pending