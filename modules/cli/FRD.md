# FRD — CLI Surface

## Feature Overview

The CLI surface is the user-facing entry point for `sdc`. It parses argv,
dispatches to the host, memory, and planner capabilities via their
contract aggregates, and renders JSON output to stdout.

## Functional Requirements

### FR-CLI-001: Subcommand Dispatch

**Description:** Parse argv and route `sdc <host|memory|validate-plan>` to the correct capability aggregate, rendering JSON output to stdout with a stable exit code.

#### Business Logic
- Validate the subcommand is one of `host`, `memory`, or `validate-plan`.
- Validate required flags and positional arguments for each subcommand.
- Route the request to the injected capability aggregate and return its result.

#### Edge Cases
- Unknown subcommand exits with code 2 and no stdout output.
- Missing required argument exits with code 2 and no stdout output.
- Unwired capability raises a classified error with its configured exit code.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `sdc <host|memory|validate-plan> [flags]` |
| **Output** | JSON on stdout, exit code on stderr |
| **Protocol** | `IHostAggregate`, `IMemoryAggregate`, `IPlanAggregate` |
| **Method** | `cmd_sdc(argv)` → `int` |
| **Event** | none |
| **Error** | `SdcError` subclasses → formatted to stderr with exit code |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Valid `sdc host setup` call | Dispatch to host agent | JSON `{python, scratch_dir, run_id}` printed to stdout, exit 0 |
| Unknown subcommand `sdc bogus` | Reject with argparse error | No stdout output, exit code 2 |
| Missing required arg `sdc host setup` | Reject with argparse error | No stdout output, exit code 2 |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Dispatch latency | < 10ms |
| Subcommand routing accuracy | 100% |

### FR-CLI-002: Host Subcommand

**Description:** Create a per-repo per-skill artifact root via `sdc host setup`, or unlink file paths via `sdc host cleanup`.

#### Business Logic
- Validate `subdir` is one of `implement`, `plan`, `execute`; reject unknown values with `HostError`.
- Resolve the repo slug from git origin remote, falling back to git toplevel dir name.
- Create `~/.agents/develop/<slug>/<subdir>/` with mode `0o700`.
- Unlink each cleanup path independently, skipping missing paths silently.

#### Edge Cases
- Not inside a git repository raises `HostError("not inside a git repository")`.
- No Python 3 interpreter found raises `HostError("no Python 3 interpreter found")`.
- Unknown subdir value raises `HostError` with the invalid value shown.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `sdc host setup --subdir <implement|plan|execute>` or `sdc host cleanup <paths...>` |
| **Output** | JSON `{python, scratch_dir, run_id}` for setup; exit 0 for cleanup |
| **Protocol** | `IHostAggregate` |
| **Method** | `HostAgent.dispatch(HostRequest) → HostResult` |
| **Event** | none |
| **Error** | `HostError` if not a git repo or unknown subdir |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Inside git repo with origin remote | `sdc host setup --subdir implement` | Directory created at `~/.agents/develop/<repo>/implement/`, JSON printed |
| Inside git repo without origin remote | `sdc host setup --subdir plan` | Slug derived from toplevel dir name, directory created |
| Not inside a git repository | `sdc host setup --subdir implement` | Error to stderr, no directory created |
| Unknown subdir value | `sdc host setup --subdir foo` | Error to stderr, no directory created |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Setup latency (p95) | < 100ms |
| Directory creation success rate | 100% |

### FR-CLI-003: Memory Subcommand

**Description:** Manage per-repo memory files: resolve path, read content, snapshot state, or update under exclusive lock.

#### Business Logic
- Resolve `~/.agents/develop/<slug>/memory/<workspace-id>.md` for path/read/snapshot/update.
- Return empty string for missing memory file on read; exit 0.
- Parse memory markdown into structured JSON snapshot with dedup and category caps.
- Merge run specs under exclusive flock (30s/0.2s) with atomic write at mode `0o600`.

#### Edge Cases
- Missing memory file returns empty content for read/snapshot with `exists: false`.
- Lock acquisition timeout raises `LockTimeoutError` with exit code 3.
- Malformed JSON on stdin raises `SpecError` with exit code 4.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `sdc memory <path|read|snapshot|update> [flags]` |
| **Output** | JSON or plain text depending on subcommand |
| **Protocol** | `IMemoryAggregate` |
| **Method** | `MemoryStore.execute(MemoryRequest) → MemoryResult` |
| **Event** | none |
| **Error** | `SpecError`, `LockTimeoutError`, `WorkspaceIdError` |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Memory file exists | `sdc memory read` | File contents printed to stdout, exit 0 |
| Memory file missing | `sdc memory read` | Empty output, exit 0 |
| Update with valid JSON spec | `sdc memory update` | Merged spec, stats returned, exit 0 |
| Lock timeout | `sdc memory update` | Error to stderr, exit code 3 |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Memory update atomicity | 100% |
| Lock acquisition success rate | 100% |

### FR-CLI-004: Validate-Plan Subcommand

**Description:** Validate the PR Plan DAG in a design document and emit a JSON validation report.

#### Business Logic
- Parse `## PR Plan` section entries from the design document.
- Validate dependency references and detect cycles in the DAG.
- Compute level assignments, max parallelism, and linearized merge order.
- Return `valid=true` with report on success; `valid=false` with errors on failure.

#### Edge Cases
- Missing `## PR Plan` section raises `PlanParseError` with exit code 4.
- Invalid DAG (cycle or missing dependency) raises `PlanValidationError` with exit code 1.
- Unreadable or missing design document raises `PlanUsageError` with exit code 2.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `sdc validate-plan <design-doc-path>` |
| **Output** | JSON report with `valid`, `pr_count`, `levels`, `max_parallelism`, `linearized_order`, `level_assignments`, `errors` |
| **Protocol** | `IPlanAggregate` |
| **Method** | `PlanValidator.execute(PlanRequest) → PlanResult` |
| **Event** | none |
| **Error** | `PlanUsageError`, `PlanValidationError` |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Valid DAG design doc | `sdc validate-plan design.md` | JSON report with `valid: true`, exit 0 |
| Cyclic DAG design doc | `sdc validate-plan design.md` | JSON report with `valid: false`, exit 1 |
| Missing PR Plan section | `sdc validate-plan design.md` | Error to stderr, exit code 4 |

#### Metric
| Target Metric | Value |
|---------------|-------|
| DAG validation accuracy | 100% |
| Plan parse latency | < 50ms |

## Public Interface

### Protocol API

- `IHostAggregate.dispatch(HostRequest) → HostResult`
- `IMemoryAggregate.execute(MemoryRequest) → MemoryResult`
- `IPlanAggregate.execute(PlanRequest) → PlanResult`

### Aggregate API

- `HostAgent` implements `IHostAggregate`
- `AgentMemory` implements `IMemoryAggregate`
- `AgentPlanner` implements `IPlanAggregate`

## Reference

- [PRD.md](../../../PRD.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](../../../ROADMAP.md)
- [ARCHITECTURE.md](../../../ARCHITECTURE.md)