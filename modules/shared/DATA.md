# DATA — Shared Kernel

## Data Requirements

### DT-SDC-001: Taxonomy Constants

| Aspect | Detail |
|--------|--------|
| Type | `taxonomy_sdc_constant.py` |
| Content | Artifact root paths, memory file config, naming patterns, exit codes |
| Consumers | All feature modules (host, memory, planner, cli) |

### DT-SDC-002: Taxonomy Errors

| Aspect | Detail |
|--------|--------|
| Type | `taxonomy_sdc_error.py` |
| Content | `SdcError`, `WorkspaceIdError`, `LockTimeoutError`, `SpecError`, `MemoryHelperError`, `HostError`, `PlanValidationError`, `PlanUsageError` |
| Consumers | All feature modules |

### DT-SDC-003: Taxonomy VOs

| Aspect | Detail |
|--------|--------|
| Type | `taxonomy_sdc_vo.py` |
| Content | `HostSetup`, `Pattern`, `RecentRun`, `PrEntry`, `PlanReport` |
| Consumers | All feature modules |

### DT-SDC-004: Common Utilities

| Aspect | Detail |
|--------|--------|
| Type | `utility_sdc_common.py` |
| Content | `resolve_python`, `slugify`, `repo_slug`, `canonicalize_remote`, `sanitize_one_line`, `normalize`, `git_output` |
| Consumers | All feature modules |

### DT-HOST-001: Host Contracts

| Aspect | Detail |
|--------|--------|
| Type | `contract_host_aggregate.py` |
| Content | `IHostAggregate` ABC |
| Consumers | `cli` module (HostHelper), `cli` surface |

### DT-MEM-001: Memory Contracts

| Aspect | Detail |
|--------|--------|
| Type | `contract_memory_aggregate.py` |
| Content | `IMemoryAggregate` ABC |
| Consumers | `memory` module (MemoryStore), `cli` surface |

### DT-PLAN-001: Planner Contracts

| Aspect | Detail |
|--------|--------|
| Type | `contract_planner_aggregate.py` |
| Content | `IPlanAggregate` ABC |
| Consumers | `planner` module (PlanValidator), `cli` surface |

## Reference

- [PRD.md](../../PRD.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](../../ROADMAP.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)