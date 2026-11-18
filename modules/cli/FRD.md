# FRD — CLI Surface

## Feature Overview

The CLI surface is the user-facing entry point for `sdc`. It parses argv,
dispatches to the host, memory, and planner capabilities via their
contract aggregates, and renders JSON output to stdout.

## Functional Requirements

### FR-CLI-001: Subcommand Dispatch

| Aspect | Detail |
|--------|--------|
| Input | `sdc <host\|memory\|validate-plan> [flags]` |
| Output | JSON on stdout, exit code on stderr |
| Protocol | `IHostAggregate`, `IMemoryAggregate`, `IPlanAggregate` |
| Method | `cmd_sdc(argv)` → `int` |
| Event | none |
| Error | `SdcError` subclasses → formatted to stderr with exit code |

### FR-CLI-002: Host Subcommand

| Aspect | Detail |
|--------|--------|
| Input | `sdc host setup --subdir <implement\|plan\|execute>` or `sdc host cleanup <paths...>` |
| Output | JSON `{python, scratch_dir, run_id}` for setup; exit 0 for cleanup |
| Protocol | `IHostAggregate` |
| Method | `HostHelper.execute(HostRequest) → HostResult` |
| Event | none |
| Error | `HostError` if not a git repo or unknown subdir |

### FR-CLI-003: Memory Subcommand

| Aspect | Detail |
|--------|--------|
| Input | `sdc memory <path\|read\|snapshot\|update> [flags]` |
| Output | JSON or plain text depending on subcommand |
| Protocol | `IMemoryAggregate` |
| Method | `MemoryStore.execute(MemoryRequest) → MemoryResult` |
| Event | none |
| Error | `SpecError`, `LockTimeoutError`, `WorkspaceIdError` |

### FR-CLI-004: Validate-Plan Subcommand

| Aspect | Detail |
|--------|--------|
| Input | `sdc validate-plan <design-doc-path>` |
| Output | JSON report with `valid`, `pr_count`, `levels`, `max_parallelism`, `linearized_order`, `level_assignments`, `errors` |
| Protocol | `IPlanAggregate` |
| Method | `PlanValidator.execute(PlanRequest) → PlanResult` |
| Event | none |
| Error | `PlanUsageError`, `PlanValidationError` |

## Public Interface

### Protocol API

- `IHostAggregate.execute(HostRequest) → HostResult`
- `IMemoryAggregate.execute(MemoryRequest) → MemoryResult`
- `IPlanAggregate.execute(PlanRequest) → PlanResult`

### Aggregate API

- `HostHelper` implements `IHostAggregate`
- `MemoryStore` implements `IMemoryAggregate`
- `PlanValidator` implements `IPlanAggregate`

## Reference

- [PRD.md](../../../PRD.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](../../../ROADMAP.md)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md)