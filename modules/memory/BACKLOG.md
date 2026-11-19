# BACKLOG — Memory Helper

## Progress Overview

The memory helper feature is implemented: per-repo memory under `~/.agents/develop/<reponame>/memory/` with path resolution, markdown read/update.

## Backlog Status

### FR-MEM-001: Resolve memory path

| Aspect       | Detail                                      |
|--------------|---------------------------------------------|
| State        | Done                                        |
| Done         | Deterministic `~/.agents/develop/<slug>/memory/<id>.md` path resolution with workspace id `^[a-z0-9._-]+-[0-9a-f]{12}$` |
| In Progress  | None                                        |
| Risk         | None                                        |
| Updated      | 2026-11-18                                  |

### FR-MEM-002: Read memory content

| Aspect       | Detail                                      |
|--------------|---------------------------------------------|
| State        | Done                                        |
| Done         | Raw UTF-8 markdown read; empty string for missing file; exit 0 |
| In Progress  | None                                        |
| Risk         | None                                        |
| Updated      | 2026-11-18                                  |

### FR-MEM-003: Return top-N issue patterns (read-only)

| Aspect       | Detail                                      |
|--------------|---------------------------------------------|
| State        | Done                                        |
| Done         | Read-only top-N count-desc patterns, optional case-insensitive category filter; missing file → empty result, exit 0; payload `{"patterns": [...], "total": N, "exists": bool}` |
| In Progress  | None                                        |
| Risk         | None                                        |
| Updated      | 2026-11-18                                  |

### FR-MEM-004: Update memory file

| Aspect       | Detail                                      |
|--------------|---------------------------------------------|
| State        | Done                                        |
| Done         | Exclusive `flock` (30s/0.2s) + atomic `tempfile.mkstemp`/`os.replace` write at `0o600`; dedup, category cap 25, recent runs cap 20; `run.workflow` rendered as `- **Workflow**: <value>` body line |
| In Progress  | None                                        |
| Risk         | None                                        |
| Updated      | 2026-11-18                                  |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| FRD          | Functional requirements specification           | [FRD.md](FRD.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |