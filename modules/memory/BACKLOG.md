# BACKLOG — Memory Helper

## Progress Overview

The memory helper feature is implemented: per-repo memory under `~/.agents/develop/<reponame>/memory/` with path resolution, markdown read/snapshot/update.

## Backlog Status

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-MEM-001 | Done | Per-repo memory root (`memory/`) under the host setup | P0 |
| BL-MEM-002 | Done | Markdown read, snapshot, and update actions | P0 |
| BL-MEM-003 | Done | Merge-on-update (append missing lines to the target section) | P0 |
| BL-MEM-004 | Done | File lock for concurrent agent writes | P0 |
| BL-MEM-005 | Done | AGENTS.md conflict check + backup before merge | P0 |
| BL-MEM-006 | Done | Canonical block markers in capability implementation | P0 |
| BL-MEM-007 | Todo | Memory migration (merge legacy `MEMORY.md` into topic files) | P2 |

## Reference

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [FRD.md](FRD.md)
- [PRD.md](../../PRD.md)
- [ROADMAP.md](../../ROADMAP.md)