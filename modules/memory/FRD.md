# FRD — Memory Store

## Feature Overview

```text
[Surface] --> [AgentMemory] --> [CapabilitiesPath / CapabilitiesReader / CapabilitiesSnapshot / CapabilitiesWriter]
[Surface] --> [utility_memory_helper] (shared stateless logic)
[AgentMemory] --> [IMemoryAggregate] (contract)
[Capabilities*] --> [IMemory*Protocol] (contract)
```

The **Memory Store** feature manages workspace-scoped review pattern memory files for the `sdc` toolchain. It resolves a deterministic per-repository memory path, reads and parses the markdown file into a structured snapshot, and merges new run patterns or issue entries under an exclusive file lock with atomic writes. The feature exposes four caller-observable actions: `path`, `read`, `snapshot`, and `update`.

## Functional Requirements

### FR-MEM-001: Resolve memory path

**Description:**
The feature shall resolve the absolute path to the memory markdown file for the active repository. The path is derived from a workspace id computed from the git origin remote URL, the git common dir, or the current working directory, in that priority order.

#### Business Logic
- The workspace id shall be constructed as `<readable-name>-<hash12>`, where `<readable-name>` is a filesystem-safe truncation of the remote slug or directory name and `<hash12>` is the first 12 hex characters of the SHA-256 digest of the canonical id source.
- The id source shall be the git origin remote URL, canonicalised by stripping the scheme, user, and `.git` suffix; hosts listed as case-insensitive (`github.com`, `gitlab.com`, `bitbucket.org`) shall have their path lowercased.
- When no origin remote is configured, the id source shall be the resolved path of the git common dir.
- When no git repo is available, the id source shall be the resolved current working directory.
- The memory directory shall be `~/.agents/develop/<repo-slug>/memory/`, created with mode `0o700` when `create_dir` is requested.
- The memory file shall be named `<workspace-id>.md`; the lock file shall be named `<workspace-id>.lock`.

#### Edge Cases
- If the git origin remote URL is unresolvable and `git rev-parse --git-common-dir` fails and the current working directory is inaccessible, the feature shall raise `WorkspaceIdError`.
- If the home directory cannot be determined, the feature shall raise `WorkspaceIdError`.
- If the repo slug cannot be resolved from git, the feature shall raise `WorkspaceIdError`.
- If directory creation fails, the feature shall raise `WorkspaceIdError` with the path and the underlying `OSError`.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | None (uses the active repository context); source: CLI `sdc memory path` |
| **Output** | Absolute file path string written to stdout |
| **Protocol** | `IMemoryPathProtocol` |
| **Method** | `resolve_paths()` |
| **Event** | none |
| **Error** | `WorkspaceIdError` when no usable id source is found, when the home directory is undeterminable, when the repo slug cannot be resolved, or when directory creation fails |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Inside a git repo with an origin remote | Call `resolve_paths()` | A path `~/.agents/develop/<repo-slug>/memory/<workspace-id>.md` is returned; `workspace-id` matches `^[a-z0-9._-]+-[0-9a-f]{12}$` |
| Inside a git repo without an origin remote | Call `resolve_paths()` | The id source falls back to the git common dir; a deterministic path is returned |
| Not inside a git repo | Call `resolve_paths()` | `WorkspaceIdError` is raised with exit code `2` |
| `create_dir=True` and directory does not exist | Call `resolve_paths(create_dir=True)` | The memory directory is created with mode `0o700` |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Path resolution latency (p95) | < 50ms |
| Workspace id determinism | 100% (same repo always yields the same id) |

### FR-MEM-002: Read memory content

**Description:**
The feature shall return the raw markdown content of the memory file. When the file does not exist, the feature shall return an empty string.

#### Business Logic
- The feature shall resolve the memory file path using the same rules as FR-MEM-001 before reading.
- The feature shall read the file as UTF-8 text.
- When the file does not exist, the feature shall return an empty string with no error raised.
- When the file exists but is empty or whitespace-only, the feature shall return the file contents as-is.

#### Edge Cases
- If the memory directory does not exist, the feature shall treat the file as missing and return an empty string.
- If the file cannot be read due to permission errors, the feature shall propagate the `OSError` to the caller.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | None (uses the resolved memory file path); source: CLI `sdc memory read` |
| **Output** | Raw markdown content string written to stdout |
| **Protocol** | `IMemoryReaderProtocol` |
| **Method** | `read_content()` |
| **Event** | none |
| **Error** | `WorkspaceIdError` when the workspace id cannot be resolved; `OSError` when the file exists but cannot be read |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Memory file exists with content | Call `read_content()` | The raw markdown content is returned verbatim |
| Memory file does not exist | Call `read_content()` | An empty string is returned; exit code is `0` |
| Memory file exists but is empty | Call `read_content()` | An empty string is returned; exit code is `0` |
| Not inside a git repo | Call `read_content()` | `WorkspaceIdError` is raised with exit code `2` |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Read latency (p95) | < 50ms |
| Missing-file handling correctness | 100% (empty string, no error) |

### FR-MEM-003: Snapshot memory state

**Description:**
The feature shall parse the memory markdown file into a structured JSON snapshot containing all common issues and recent runs. When the file does not exist, the snapshot shall indicate `exists: false`.

#### Business Logic
- The feature shall parse the markdown file into three sections: header lines, common issues (grouped by category), and recent runs (with date, description, and body lines).
- The snapshot payload shall contain `common_issues` as a flat list of `{category, description, count}` objects, `recent_runs` as a list of `{date, description, body_lines}` objects, and `exists` as a boolean.
- When the memory file does not exist, `common_issues` shall be an empty list, `recent_runs` shall be an empty list, and `exists` shall be `false`.
- Category matching during parse shall be case-insensitive and whitespace-normalised.
- Issue descriptions shall be matched for dedup using lowercase, trailing-punctuation-stripped, whitespace-collapsed normalisation.

#### Edge Cases
- If the markdown file is malformed (e.g., an issue line without a preceding category heading), the parser shall skip the unmatched line and continue.
- If the file exists but contains only the default header with no issue or run sections, the snapshot shall return empty lists with `exists: true`.
- If the file is empty or whitespace-only, the snapshot shall return empty lists with `exists: true`.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | None (uses the resolved memory file path); source: CLI `sdc memory snapshot` |
| **Output** | JSON object `{common_issues: [...], recent_runs: [...], exists: bool}` written to stdout |
| **Protocol** | `IMemorySnapshotProtocol` |
| **Method** | `read_snapshot()` |
| **Event** | none |
| **Error** | `WorkspaceIdError` when the workspace id cannot be resolved |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Memory file exists with issues and runs | Call `read_snapshot()` | JSON contains populated `common_issues` and `recent_runs` arrays and `exists: true` |
| Memory file does not exist | Call `read_snapshot()` | JSON contains empty `common_issues` and `recent_runs` arrays and `exists: false` |
| Memory file exists with only the default header | Call `read_snapshot()` | JSON contains empty `common_issues` and `recent_runs` arrays and `exists: true` |
| Not inside a git repo | Call `read_snapshot()` | `WorkspaceIdError` is raised with exit code `2` |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Snapshot latency (p95) | < 50ms |
| Parse fidelity (issues + runs correctly extracted) | 100% |

### FR-MEM-004: Update memory file

**Description:**
The feature shall merge a run specification into the memory markdown file under an exclusive file lock, then write the updated content atomically. The merge shall deduplicate issue patterns, cap categories and recent runs to their configured limits, and return summary statistics.

#### Business Logic
- The feature shall acquire an exclusive `flock` on the lock file before reading the existing memory file, with a timeout of 30 seconds and a poll interval of 0.2 seconds.
- The input spec shall be a JSON object with optional `patterns` (list of `{category, description}` objects) and optional `run` (object with `date`, `description`, `rounds`, `issues_by_severity`, `key_patterns`, `specializations`).
- When a pattern description matches an existing entry (case-insensitive, punctuation-stripped, whitespace-collapsed), the feature shall increment its count rather than appending a duplicate.
- When the number of patterns in a category exceeds `MAX_PATTERNS_PER_CATEGORY` (25), the feature shall sort by descending count then ascending description and truncate the lowest-count entries.
- When the number of recent runs exceeds `MAX_RECENT_RUNS` (20), the feature shall drop the oldest entries.
- The memory file shall be written atomically via `tempfile.mkstemp` + `os.replace`, with mode `0o600`.
- The return payload shall include `file` (absolute path), `existed_before` (boolean), `stats` (merge counters), `total_categories`, `total_patterns`, and `total_recent_runs`.

#### Edge Cases
- If the spec is empty or not a dict, the feature shall raise `SpecError` with exit code `4`.
- If `patterns` is not a list, the feature shall raise `SpecError`.
- If a pattern entry is not an object, or its `category`/`description` fields have the wrong type, the feature shall raise `SpecError`.
- If `run.date` is provided but not a calendar-valid `YYYY-MM-DD` string, the feature shall raise `SpecError`.
- If the exclusive lock cannot be acquired within 30 seconds, the feature shall raise `LockTimeoutError` with exit code `3`.
- If the lock file cannot be opened, the feature shall raise `MemoryHelperError` with exit code `1`.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | JSON spec object on stdin or `--file` path; source: CLI `sdc memory update` |
| **Output** | JSON object `{file, existed_before, stats, total_categories, total_patterns, total_recent_runs}` written to stdout |
| **Protocol** | `IMemoryWriterProtocol` |
| **Method** | `update(spec)` |
| **Event** | `memory_updated` |
| **Error** | `SpecError` (exit 4) for malformed spec; `LockTimeoutError` (exit 3) when lock cannot be acquired within 30s; `MemoryHelperError` (exit 1) for lock file I/O errors |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Memory file exists, spec contains new patterns | Call `update(spec)` | Patterns are appended; `stats.new_patterns` reflects the count; file is written atomically |
| Memory file exists, spec contains duplicate patterns | Call `update(spec)` | Duplicate counts are incremented; `stats.merged_patterns` reflects the count; no duplicate lines are written |
| Memory file does not exist, spec contains patterns | Call `update(spec)` | File is created with the default header plus the new patterns; `existed_before` is `false` |
| Category exceeds 25 patterns after merge | Call `update(spec)` | Lowest-count entries are dropped; `stats.categories_capped` records the dropped count per category |
| More than 20 recent runs after merge | Call `update(spec)` | Oldest runs are dropped; `stats.recent_runs_dropped` records the count |
| Spec is empty or not a dict | Call `update({})` | `SpecError` is raised with exit code `4` |
| Another process holds the lock for more than 30 seconds | Call `update(spec)` | `LockTimeoutError` is raised with exit code `3` |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Update latency (p95, no contention) | < 100ms |
| Dedup correctness | 0 duplicate entries after merge |
| Atomic write success rate | 100% |
| Lock timeout accuracy | 100% (raises within 30s ± 0.2s) |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | `AgentMemory`     |
| Aggregate  | `IMemoryAggregate` |
| Method     | `execute(request)` |
| Request    | `MemoryRequest`   |
| Response   | `MemoryResult`    |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |