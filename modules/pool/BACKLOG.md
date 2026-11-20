# BACKLOG — Pool Helper

## Progress Overview

The pool helper feature is complete: `sdc pool grok <session-id>` polls a Grok Build session running in an Orca terminal and detects completion (sentinel, final-report on idle, terminal exit, or deadline), wired on the AES 7-layer architecture through the `sdc` surface.

## Backlog Status

### FR-POOL-001: Poll a Grok Build session (single probe)

| Aspect       | Detail                                                                 |
|--------------|------------------------------------------------------------------------|
| State        | Done                                                                   |
| Done         | `CapabilitiesPoolGrok.poll()` performs one rendered-screen read; reports done/running/failed/unknown |
| In Progress  | None                                                                   |
| Risk         | None                                                                   |
| Updated      | 2026-11-20                                                             |

### FR-POOL-002: Wait until completion (blocking mode)

| Aspect       | Detail                                                                 |
|--------------|------------------------------------------------------------------------|
| State        | Done                                                                   |
| Done         | `--wait` blocks until done/failure/deadline with `idle_confirm` cycles |
| In Progress  | None                                                                   |
| Risk         | None                                                                   |
| Updated      | 2026-11-20                                                             |

### FR-POOL-003: Unknown agent or action rejected

| Aspect       | Detail                                                                 |
|--------------|------------------------------------------------------------------------|
| State        | Done                                                                   |
| Done         | `AgentPool.execute` raises `PoolUsageError` for unknown agent/action   |
| In Progress  | None                                                                   |
| Risk         | None                                                                   |
| Updated      | 2026-11-20                                                             |

## Reference

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [FRD.md](FRD.md)
- [PRD.md](../../PRD.md)
- [ROADMAP.md](../../ROADMAP.md)
