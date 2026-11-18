# FRD — Host Helper

## Feature Overview

The host helper capability manages per-repo artifact roots under
`~/.agents/develop/<reponame>/<subdir>/` for the implement, design, and
execute-plan skills.

## Functional Requirements

### FR-HOST-001: Setup

| Aspect | Detail |
|--------|--------|
| Input | `--subdir <implement\|plan\|execute>` |
| Output | JSON `{python, scratch_dir, run_id}` |
| Protocol | `IHostAggregate` |
| Method | `HostHelper.execute(HostRequest(action="setup", subdir=...))` |
| Event | none |
| Error | `HostError` if not a git repo or unknown subdir |

### FR-HOST-002: Cleanup

| Aspect | Detail |
|--------|--------|
| Input | list of file paths |
| Output | exit 0 (or 1 if any unlink failed) |
| Protocol | `IHostAggregate` |
| Method | `HostHelper.execute(HostRequest(action="cleanup", paths=...))` |
| Event | none |
| Error | prints warning for each failed unlink, continues |

## Public Interface

### Protocol API

- `IHostAggregate.execute(HostRequest) → HostResult`

### Aggregate API

- `HostHelper` implements `IHostAggregate`

## Reference

- [PRD.md](../../PRD.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](../../ROADMAP.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)