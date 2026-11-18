# FRD — Host Helper

## Feature Overview

```text
[Surface] --> [HostAgent] --> [HostSetup / HostCleanup]
[Surface] --> [utility_host_helper] (shared stateless logic)
[HostAgent] --> [IHostAggregate] (contract)
[HostSetup] --> [IHostSetupProtocol] (contract)
[HostCleanup] --> [IHostCleanupProtocol] (contract)
```

The **Host Helper** feature provides per-repository artifact management for the implement, planner, and execute-plan skills. It creates isolated per-skill artifact directories under `~/.agents/develop/<repo-slug>/<subdir>/` and unlinks temporary files when those skills complete. The feature exposes two caller-observable behaviours: creating a fresh artifact root with a setup result, and cleaning up a list of file paths with a per-file failure count.

Capabilities are injected into the agent via `HostAgent.create()` constructor injection: `HostAgent.create(setup_cap=..., cleanup_cap=...)` wires the setup and cleanup capabilities into the orchestrator at construction time.

## Functional Requirements

### FR-HOST-001: Setup artifact root

**Description:**
The feature shall create the per-repo, per-skill artifact root directory `~/.agents/develop/<reponame>/<subdir>/` (mode `0o700`) and return the Python interpreter path, the absolute scratch directory, and a short run id to the caller. The repository slug is resolved from the git origin remote, falling back to the git toplevel directory name when no remote is configured.

#### Business Logic
- The repository slug must be derived from `git remote get-url origin`, with the `.git` suffix and path components stripped so `https://github.com/user/my-repo.git` yields `my-repo`.
- When no origin remote is configured, the feature shall fall back to the name of the directory returned by `git rev-parse --show-toplevel`.
- The subdir value must be one of `implement`, `plan`, or `execute`; any other value causes the feature to raise `HostError`.
- The scratch directory shall be created with mode `0o700`; failure to chmod shall not fail the setup operation.
- The run id shall be an 8-character lowercase hexadecimal string generated fresh on every setup call.
- The Python interpreter path shall be the absolute path to a Python 3 interpreter found on the host.

#### Edge Cases
- If the current directory is not inside a git repository, the feature shall raise `HostError("not inside a git repository")` and shall not create any directory.
- If no Python 3 interpreter is found on the system, the feature shall raise `HostError("no Python 3 interpreter found")`.
- If `git remote get-url origin` returns a non-zero exit code but `git rev-parse --show-toplevel` succeeds, the slug shall be derived from the local directory name instead of failing.
- If the origin remote URL is malformed or yields an empty slug after normalisation, the feature shall fall back to the git toplevel directory name.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | `subdir` value (`implement`, `plan`, or `execute`); source: CLI `--subdir` flag |
| **Output** | JSON object `{python, scratch_dir, run_id}` written to stdout; `run_id` is an 8-hex-character string |
| **Protocol** | `IHostSetupProtocol` |
| **Method** | `setup(subdir)` |
| **Event** | `scratch_dir_created` |
| **Error** | `HostError` when the directory is not inside a git repository, when no Python 3 interpreter is found, or when `subdir` is not one of the three valid values |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Inside a git repository with an origin remote | Call setup with subdir `implement` | A directory is created at `~/.agents/develop/<reponame>/implement/` with mode `0o700`; JSON with `python`, `scratch_dir`, and `run_id` is printed to stdout |
| Inside a git repository without an origin remote | Call setup with subdir `plan` | The slug is derived from the git toplevel directory name; a directory is created at `~/.agents/develop/<reponame>/plan/`; JSON is printed |
| Not inside a git repository | Call setup with any subdir | An error is returned to stderr and no directory is created |
| Unknown subdir value | Call setup with subdir `foo` | An error is returned to stderr and no directory is created |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Setup latency (p95) | < 100ms |
| Directory creation success rate | 100% |

#### Performance Test
The setup latency p95 is asserted at **< 100ms** using a `time.perf_counter()` loop over 1000 iterations. The test collects per-call durations in milliseconds, sorts them, and asserts the 95th-percentile value stays under the 100ms threshold.

#### Error Message Format Tests
- Unknown subdir: asserts `HostError` message contains `host: unknown subdir` and the repr of the invalid value (e.g. `'foo'`).
- Not inside a git repository: asserts `HostError` message contains `not inside a git repository`.

### FR-HOST-002: Cleanup paths

**Description:**
The feature shall unlink each file path passed by the caller independently. Missing paths are skipped silently. The caller receives an exit code indicating whether any unlink failed, so partial failures are visible without halting remaining operations.

#### Business Logic
- Each path shall be unlinked independently; one failure shall not prevent the remaining paths from being processed.
- A path that does not exist shall be treated as success with no error raised.
- Any unlink failure shall be reported to stderr with the path and the underlying `OSError` message, without stopping the remaining unlink operations.
- The exit code shall be `0` when all paths are successfully unlinked or do not exist; `1` when at least one unlink fails.

#### Edge Cases
- If none of the provided paths exist, the feature shall return exit code `0` with no output.
- If a path is a directory rather than a regular file, the unlink shall fail and the error shall be reported to stderr, but other paths shall still be processed.
- If file permissions prevent unlink, the failure shall be reported to stderr and the exit code shall be `1`.
- If zero paths are provided, the CLI surface shall reject the invocation before dispatch.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | One or more file paths; source: CLI positional arguments |
| **Output** | Process exit code: `0` = all paths removed or absent, `1` = at least one unlink failed |
| **Protocol** | `IHostCleanupProtocol` |
| **Method** | `cleanup(paths)` |
| **Event** | none |
| **Error** | Each failed unlink shall print `host: could not remove <path>: <os error>` to stderr; exit code `1` |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| All paths exist | Call cleanup with 3 existing file paths | All 3 files are removed; exit code is `0` |
| Some paths are missing | Call cleanup with 2 existing + 1 missing path | The 2 existing files are removed; the missing path is skipped; exit code is `0` |
| One path is a directory | Call cleanup with 1 writable file + 1 directory | The writable file is removed; the directory unlink fails and the error is printed to stderr; exit code is `1` |
| All paths are missing | Call cleanup with 3 non-existent paths | No files are removed; exit code is `0` |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Cleanup exit code correctness | 100% |
| Partial failure visibility (stderr coverage) | 100% of failures reported to stderr |

#### Error Message Format Tests
- Each failed unlink asserts `host: could not remove <path>: <os error>` appears on stderr.
- Zero paths: asserts empty stderr (no false-positive error messages).
- Multiple failures: asserts each failing path produces a separate stderr line.

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | `HostAgent`       |
| Aggregate  | `IHostAggregate`  |
| Method     | `dispatch(request)` |
| Request    | `HostRequest`     |
| Response   | `HostResult`      |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |