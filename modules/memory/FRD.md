# FRD — Memory Store

## Feature Overview

The memory store capability manages workspace-scoped review pattern
memory files with concurrency-safe atomic writes and deterministic dedup.

## Functional Requirements

### FR-MEM-001: Path Resolution

| Aspect | Detail |
|--------|--------|
| Input | git remote origin URL or git toplevel dir or cwd |
| Output | `~/.agents/implement-memory/<workspace-id>.md` |
| Protocol | `IMemoryAggregate` |
| Method | `MemoryStore.execute(MemoryRequest(action="path"))` |
| Event | none |
| Error | `WorkspaceIdError` if no usable source |

### FR-MEM-002: Read

| Aspect | Detail |
|--------|--------|
| Input | none (uses resolved path) |
| Output | file contents (empty if missing) |
| Protocol | `IMemoryAggregate` |
| Method | `MemoryStore.execute(MemoryRequest(action="read"))` |
| Event | none |
| Error | `WorkspaceIdError` |

### FR-MEM-003: Snapshot

| Aspect | Detail |
|--------|--------|
| Input | none (uses resolved path) |
| Output | parsed JSON `{common_issues, recent_runs, exists}` |
| Protocol | `IMemoryAggregate` |
| Method | `MemoryStore.execute(MemoryRequest(action="snapshot"))` |
| Event | none |
| Error | `WorkspaceIdError` |

### FR-MEM-004: Update

| Aspect | Detail |
|--------|--------|
| Input | JSON spec on stdin or `--file` path |
| Output | summary stats `{file, existed_before, stats, totals}` |
| Protocol | `IMemoryAggregate` |
| Method | `MemoryStore.execute(MemoryRequest(action="update", spec=...))` |
| Event | none |
| Error | `SpecError`, `LockTimeoutError`, `MemoryHelperError` |

## Public Interface

### Protocol API

- `IMemoryAggregate.execute(MemoryRequest) → MemoryResult`

### Aggregate API

- `MemoryStore` implements `IMemoryAggregate`

## Reference

- [PRD.md](../../PRD.md)
- [BACKLOG.md](BACKLOG.md)
- [ROADMAP.md](../../ROADMAP.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)