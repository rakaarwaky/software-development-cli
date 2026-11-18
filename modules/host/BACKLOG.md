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

## Quality Metrics

### Test Coverage

| Test File | Test Classes | Tests | Status |
|-----------|-------------|-------|--------|
| `tests/conftest.py` | Fixtures | — | Passing |
| `tests/test_capabilities_host_setup.py` | 7 | 14 | Passing |
| `tests/test_capabilities_host_cleanup.py` | 5 | 7 | Passing |
| `tests/test_agent_host_orchestrator.py` | 5 | 6 | Passing |

- **Total tests:** 27 (25 standard + 2 environment-gated)
- **Pass rate:** 100% (all tests passing on Linux)
- **Framework:** `pytest`
- **Markers:** Performance test requires Linux (`@pytest.mark.skipif` guards non-Linux platforms)

### Coverage Notes

- **FR-HOST-001 (Setup):** Covers setup with/without remote, all three valid subdirs, unknown subdir error, not-in-git-repo error, run_id uniqueness, 8-hex format, directory mode `0o700`, and p95 latency.
- **FR-HOST-002 (Cleanup):** Covers all-existing, partial-missing, directory-as-path, all-missing, empty-list, and exact stderr message format assertions.
- **Orchestrator:** Covers setup dispatch, cleanup dispatch, unknown action `HostError` (not `ValueError`), `paths=None` vs empty-list guard, and constructor injection.

### Platform-Specific Notes

- **BL-HOST-005 (Windows support):** Not yet implemented. All tests assume POSIX/Linux (`os.name != "posix"` skip). Windows-specific tests will be needed for:
  - File locking / unlink behavior differences
  - Path separator handling
  - Permission model (`0o700` → Windows ACL)
  - Git subprocess availability