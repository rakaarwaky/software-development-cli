# BACKLOG — Host Helper

## Progress Overview

The host helper feature is complete: per-repo artifact roots under `~/.agents/develop/<reponame>/<subdir>/` are set up and cleaned for the implement, design, and execute-plan skills.

## Backlog Status

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-HOST-001 | Done | Setup with subdir parameter | P0 |
| BL-HOST-002 | Done | Cleanup with path list | P0 |
| BL-HOST-003 | Done | Repo slug resolution (remote → toplevel) | P0 |
| BL-HOST-004 | Done | Python interpreter resolution (Linux only) | P0 |
| BL-HOST-005 | Todo | Windows support | P3 |

## Reference

- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [FRD.md](FRD.md)
- [PRD.md](../../PRD.md)
- [ROADMAP.md](../../ROADMAP.md)

### FR-HOST-001: Setup artifact root

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `capabilities_host_setup.py` creates per-repo artifact root `~/.agents/develop/<reponame>/<subdir>/` with mode `0o700` |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |

### FR-HOST-002: Cleanup paths

| Aspect       | Detail                                       |
|--------------|----------------------------------------------|
| State        | Done                                         |
| Done         | `capabilities_host_cleanup.py` unlinks file paths independently and reports per-file failures |
| In Progress  | None                                         |
| Risk         | None                                         |
| Updated      | 2026-11-18                                   |