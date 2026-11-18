# BACKLOG — Memory Store

## Backlog

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-MEM-001 | Done | Path resolution (git remote → common dir → cwd) | P0 |
| BL-MEM-002 | Done | Read subcommand | P0 |
| BL-MEM-003 | Done | Snapshot subcommand | P0 |
| BL-MEM-004 | Done | Update with fcntl locking + atomic write | P0 |
| BL-MEM-005 | Done | Deterministic dedup + compaction | P0 |
| BL-MEM-006 | Todo | Windows msvcrt.locking test coverage | P2 |

## Done

- All subcommands ported from `scripts/memory.py`
- fcntl locking on POSIX, msvcrt locking on Windows
- Atomic temp-file + rename writes
- Deterministic dedup via normalize() + category canonicalization

## Next

- Windows CI coverage
- Performance profiling for large memory files