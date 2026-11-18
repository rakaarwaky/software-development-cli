# FRD — Host Helper

## Feature Overview

```text
[Surface] --> [HostAgent] --> [HostImplement / HostDesign / HostExecute]
[Surface] --> [utility_host_helper] (shared stateless logic)
[HostAgent] --> [IHostProtocol] (contract)
```

The **Host Helper** feature manages per-repo artifact roots under
`~/.agents/develop/<reponame>/<subdir>/` for the implement, design, and
execute-plan skills. It is called by the CLI surface through the Host Agent
and returns a JSON payload `{python, scratch_dir, run_id}` for setup.

## Functional Requirements

### FR-HOST-001: Setup artifact root

**Description:**
The feature shall create the per-repo, per-skill artifact root directory
`~/.agents/develop/<reponame>/<subdir>/` (mode `0o700`) and return the
Python interpreter path, the absolute scratch directory, and a short run id
to the caller.

#### Business Logic
- The repository slug is derived from `git remote get-url origin`, falling
  back to the git toplevel directory name when no remote is configured.
- The subdir must be one of `implement`, `plan`, or `execute`.
- The scratch directory is created with mode `0o700`; failure to chmod does
  not fail the operation.
- The run id is an 8-hex character value generated per setup call.

#### Edge Cases
- If the current directory is not inside a git repository, the feature
  returns an error and does not create a directory.
- If no Python 3 interpreter is found, the feature returns an error.
- If `git remote get-url origin` is unavailable but `git rev-parse
  --show-toplevel` succeeds, the slug is derived from the local directory
  name instead of failing.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | Subdir value (`implement`, `plan`, or `execute`); source: CLI flag |
| **Output** | JSON `{python, scratch_dir, run_id}`; destination: stdout |
| **Protocol** | `IHostProtocol` |
| **Method** | `execute` |
| **Event** | `scratch_dir_created` |
| **Error** | `HostError` when not in a git repo or unknown subdir |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Inside a git repo with origin remote | Call setup with subdir `implement` | A directory is created at `~/.agents/develop/<reponame>/implement/` and JSON with `python`, `scratch_dir`, `run_id` is printed |
| Inside a git repo without origin remote | Call setup with subdir `plan` | Slug falls back to the git toplevel directory name; directory is created |
| Not inside a git repo | Call setup with any subdir | An error is returned and no directory is created |
| Unknown subdir value | Call setup with subdir `foo` | An error is returned; no directory is created |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Setup latency | < 100ms |
| Directory creation success rate | 100% |

### FR-HOST-002: Cleanup paths

**Description:**
The feature shall unlink each file path passed by the caller. Missing paths
are skipped silently. The caller receives an exit code indicating whether
any unlink failed.

#### Business Logic
- Each path is unlinked independently; one failure does not prevent others
  from being unlinked.
- Missing paths are treated as success (no error raised).
- Any unlink failure is reported to stderr without stopping the remaining
  unlink operations.
- The exit code is 0 when all paths are unlinked or missing, 1 when at
  least one unlink fails.

#### Edge Cases
- If none of the paths exist, the feature returns exit code 0.
- If a path is a directory rather than a file, the unlink fails and is
  reported but other paths are still processed.
- If permissions prevent unlink, the failure is reported to stderr and the
  exit code reflects the failure.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | One or more file paths; source: CLI arguments |
| **Output** | Exit code (0 = success, 1 = at least one failure); destination: process exit code |
| **Protocol** | `IHostProtocol` |
| **Method** | `execute` |
| **Event** | none |
| **Error** | `OSError` reported to stderr per failed unlink; exit code 1 |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| All paths exist | Call cleanup with 3 existing paths | All 3 paths are removed; exit code 0 |
| Some paths missing | Call cleanup with 2 existing + 1 missing path | 2 existing paths removed; missing skipped; exit code 0 |
| One unlink fails | Call cleanup with 1 writable + 1 read-only path | Writable path removed; read-only path reported to stderr; exit code 1 |
| No paths provided | Call cleanup with zero paths | No operation; exit code 0 |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Cleanup exit code correctness | 100% |
| Partial failure visibility | 100% of failures reported to stderr |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | `HostAgent`       |
| Aggregate  | `IHostProtocol`   |
| Method     | `execute`         |
| Request    | `HostRequest`     |
| Response   | `HostResult`      |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |