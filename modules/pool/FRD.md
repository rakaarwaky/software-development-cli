# FRD — Pool Helper

## Feature Overview

```text
[Surface] --> [AgentPool] --> [CapabilitiesPoolGrok] --> (orca terminal)
[AgentPool] --> [IPoolAggregate] (contract)
[CapabilitiesPoolGrok] --> [IPoolGrokProtocol] (contract)
[CapabilitiesPoolGrok] --> [utility_pool_helper] (shared stateless logic)
```

The **Pool Helper** feature standardizes how an agent like Hermes polls a Grok Build session running in an Orca terminal. A full-screen TUI agent renders to its terminal *screen*, not the PTY line stream, so polling reads the rendered screen with `orca terminal read --screen --json` and paces with `orca terminal wait --for tui-idle`.

Completion is detected from either:
- a configured completion sentinel on the screen (default `EXECUTE_PLAN_COMPLETE`), or
- a final-report shape on an idle screen (a PR marker plus a settled prompt).

Idle alone never means done, and a busy (unsatisfied) wait is not an error — polling continues until completion, failure, deadline, or a single probe.

The agent author's example `sdc pool --grok <sessionid>` is realized as `sdc pool grok <session-id>` (subcommand form, consistent with `sdc host setup --subdir implement`), with optional `--wait`, `--deadline-hours`, `--wait-ms`, `--idle-confirm`, `--sentinel`, `--tail`, and `--orca` flags.

Capabilities are injected into the agent via `AgentPool.create(grok_cap=...)`. The feature emits progress lines to stderr so background notifies stay useful.

## Functional Requirements

### FR-POOL-001: Poll a Grok Build session (single probe)

**Description:**
The feature shall poll a Grok Build Orca terminal session once and return a `PoolResult` describing whether the session is done, running, failed, or unknown. With no `--wait` flag the call returns after one rendered-screen read; it never blocks.

#### Business Logic
- `sdc pool grok <session-id>` (no `--wait`) performs one `orca terminal read --screen --json` against the named terminal handle.
- If the completion sentinel is on the screen, status is `done` with `sentinel=true`.
- If the terminal has exited, status is `done` when a final report is present on screen else `failed`; `final_report` records which.
- If the session is still running, status is `running`.
- If the orca CLI cannot be read, status is `unknown`.
- Output is a JSON object to stdout with keys `session`, `status`, `sentinel`, `final_report`, `terminal_status`, `timed_out`, `cycles`, `cli_errors`, `tail`.

#### Edge Cases
- Terminal handle does not exist → `status=unknown` (no crash).
- Sentinel absent and terminal running → `status=running` with empty/small tail.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `session_id` (positional); source: CLI `sdc pool grok <session-id>` |
| **Output** | JSON object printed to stdout |
| **Protocol** | `IPoolGrokProtocol` |
| **Method** | `poll(request)` |
| **Event** | none |
| **Error** | `PoolError` when no orca CLI resolves; exit code 1 |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Session running, no sentinel | `sdc pool grok <sid>` | JSON `{status: "running", ...}` to stdout; exit code 0 |
| Sentinel on screen | `sdc pool grok <sid>` | JSON `{status: "done", sentinel: true}`; exit code 0 |
| Terminal exited with final report | `sdc pool grok <sid>` | JSON `{status: "done", final_report: true}`; exit code 0 |
| Terminal exited without final report | `sdc pool grok <sid>` | JSON `{status: "failed"}`; exit code 1 |
| orca CLI unavailable | `sdc pool grok <sid>` | Error to stderr; exit code 1 |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Single-probe latency (p95) | < 200ms |

### FR-POOL-002: Wait until completion (blocking mode)

**Description:**
With `--wait`, the feature shall block until completion, failure, terminal exit, or deadline, re-polling every `POOL_PAUSE_SECONDS` (default 10s) and pacing each cycle with `orca terminal wait --for tui-idle --timeout-ms <wait-ms>`.

#### Business Logic
- A wait cycle that is `tui-idle` satisfied AND shows a final report counts as one `idle_confirm` cycle; `idle_confirm` consecutive cycles (default 2) declare `done`.
- A busy cycle (wait not satisfied) resets `idle_confirm` to 0 and continues; it is not an error.
- Deadline default is 2 hours (`--deadline-hours`); on expiry status is `running` with `timed_out=true` and exit code 3.
- Terminal exit without a final report declares `failed` and exit code 1.
- `--sentinel`, `--wait-ms`, `--idle-confirm`, `--tail`, `--orca` override defaults.

#### Edge Cases
- Deadline of 0 (not allowed by CLI) → rejected as usage error by `_positive_int`.
- `--wait-ms` 0 → wait returns immediately; treated as busy cycle.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `session_id` + `--wait` flag (+ pacing overrides); source: CLI flags |
| **Output** | JSON object printed to stdout |
| **Protocol** | `IPoolGrokProtocol` |
| **Method** | `poll(request)` |
| **Event** | progress lines to stderr |
| **Error** | `PoolError` after `MAX_CONSECUTIVE_CLI_ERRORS` (default 10) consecutive CLI failures; exit code 1 |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Session completes before deadline | `sdc pool grok --wait <sid>` | blocks until done; exit code 0 |
| Deadline elapsed | `sdc pool grok --wait --deadline-hours 0` | `status=running`, `timed_out=true`; exit code 3 |
| 10 consecutive CLI failures | `sdc pool grok --wait <sid>` | `PoolError`; exit code 1 |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Deadline enforcement correctness | 100% |
| Wait-pacing interval | `POOL_PAUSE_SECONDS` (default 10s) |

### FR-POOL-003: Unknown agent or action rejected

**Description:**
The feature shall reject unknown agents or actions with `PoolUsageError` (exit code 2), never dispatching to an unsupported capability.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `session_id` + `action` / `agent` on `PoolRequest`; source: CLI `sdc pool grok <session-id>` |
| **Output** | `PoolUsageError` raised (exit code 2), never dispatched |
| **Protocol** | `IPoolAggregate` |
| **Method** | `execute(request)` |
| **Event** | none |
| **Error** | `PoolUsageError` (exit code 2) when the agent or action is unknown |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | `AgentPool`       |
| Aggregate  | `IPoolAggregate`  |
| Protocol   | `IPoolGrokProtocol` |
| Method     | `execute(request)` / `poll(request)` |
| Request    | `PoolRequest`     |
| Response   | `PoolResult`      |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |
