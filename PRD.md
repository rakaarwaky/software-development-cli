# PRD — software-development-cli

## Project Overview

    [Skills] --> [sdc CLI] --> [Host / Memory / Planner capabilities]

**software-development-cli (`sdc`)** is a project that consolidates the helper
scripts used by the `software-development` skills (`implement`, `design`,
`execute-plan`) into one stdlib-only Python CLI. It serves skill authors and
maintainers who need one uniform command surface instead of per-skill
`python3 .../scripts/*.py` calls. The project matters because every new skill
currently repeats its own helper-script plumbing, and skill step files grow
noisy with absolute script paths; without `sdc`, maintenance cost scales with
each added skill.

## Goals

- One `sdc` command with the `host`, `memory`, and `validate-plan` subcommands replaces every per-skill helper script.
- Skill step files invoke `sdc ...` instead of `python3 .../scripts/*.py`, keeping them thin and consistent.
- The codebase passes the AES 7-layer architecture scan with zero CRITICAL and zero HIGH violations.
- The tool runs on Python 3.9+ stdlib alone, with no third-party runtime dependencies.

## Non-Goals

- No MCP server; skills call `sdc` directly.
- No Windows support; the tool targets Linux hosts, matching the original `host.py` constraint.
- No web UI or API server.

## Target Users

| Persona | Need | Current Pain | Desired Outcome |
|---------|------|--------------|-----------------|
| Skill author | A uniform CLI for host setup, memory, and plan validation across skills | Repeats helper-script plumbing per skill | Writes skill step files that call `sdc` subcommands |
| Skill maintainer | One place to change host/memory/plan behavior | Patches several `scripts/*.py` copies per repo | Changes `modules/` once and re-installs `sdc` |
| CI maintainer | Reproducible gates for the tool | No single lint/test/type-check entry point | Runs the documented `pytest` + `mypy` + `lint-arwaky-cli` gates |

## Scope

### In Scope

- `sdc host setup|cleanup` for per-repo artifact directories.
- `sdc memory path|read|snapshot|update` for per-repo memory files.
- `sdc validate-plan` for PR-plan DAG validation.
- AES 7-layer module layout under `modules/` with the quality gates from `AGENTS.md`.

### Out of Scope

- Windows support.
- MCP server or API server surfaces.
- Web UI.

---

## Project Requirements

### PR-SDC-001: CLI Surface

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | to call `sdc host|memory|validate-plan` with flags | skill step files stay thin | P0 |

#### Proposed Solution

A single `sdc` entry point parses argv, dispatches each subcommand to its
contract aggregate, and renders JSON output to stdout with exit codes 0/1/2/3/4.

#### Main User Flow

1. Author writes `sdc host setup --subdir implement` in a skill step file.
2. `sdc` parses the subcommand and dispatches to the host aggregate.
3. `sdc` prints the JSON result and exits with the aggregate's code.

### PR-SDC-002: Host Helper

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | to create per-repo artifact directories with a subdir parameter | each skill gets an isolated scratch area | P1 |

#### Proposed Solution

`sdc host setup --subdir <implement|plan|execute>` creates
`~/.agents/develop/<reponame>/<subdir>/` and prints JSON
`{python, scratch_dir, run_id}`. `sdc host cleanup <paths...>` unlinks each
given path and skips missing ones.

#### Main User Flow

1. Skill step calls `sdc host setup --subdir implement` at session start.
2. `sdc` resolves the repo slug and Python interpreter, creates the directory, and prints JSON.
3. Skill step calls `sdc host cleanup <paths...>` at session end.

### PR-SDC-003: Memory Helper

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | to read and merge structured memory per repo | agents keep persistent notes across sessions | P1 |

#### Proposed Solution

`sdc memory path|read|snapshot|update` manages a per-repo memory file under
`~/.agents/develop/<reponame>/memory/`. `update` merges a JSON spec from stdin
(or `--file`) into the file under an exclusive lock, skipping lines that
already exist.

#### Main User Flow

1. Skill step calls `sdc memory path` to learn where memory lives.
2. Skill step calls `sdc memory read` or `sdc memory snapshot` to load it.
3. Skill step pipes a JSON spec into `sdc memory update` to merge new notes.

### PR-SDC-004: Planner Helper

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | to validate a PR-plan DAG before execution | execution runs only acyclic, dependency-complete plans | P1 |

#### Proposed Solution

`sdc validate-plan <design-doc-path>` parses the `## PR Plan` section of a
design document, validates the dependency DAG (unique IDs, valid references,
no cycles), computes level assignments, and reports max parallelism as JSON.

#### Main User Flow

1. Author saves a design document with a `## PR Plan` section.
2. Author runs `sdc validate-plan <design-doc-path>`.
3. `sdc` prints a JSON report with `valid`, `pr_count`, `levels`, `max_parallelism`, and any errors.

### PR-SDC-005: AES Architecture Compliance

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| CI maintainer | to enforce the AES 7-layer contract on every change | the codebase stays navigable for agents | P2 |

#### Proposed Solution

The `modules/` tree follows the AES 7-layer architecture with taxonomy,
contract, capabilities, agent, surface, and root layers wired from a root
entry. CI runs `lint-arwaky-cli scan modules`, `pytest`, and `mypy` on every PR.

#### Main User Flow

1. Contributor edits files under `modules/`.
2. Contributor runs `lint-arwaky-cli scan modules` and `python3 -m pytest modules/ -q` locally.
3. CI repeats the gates; the PR merges only when all pass.

### PR-SDC-006: Installer and Skill Migration

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill maintainer | to install `sdc` into `~/.local/bin` and migrate skill references | skills call `sdc` from a stable XDG path | P2 |

#### Proposed Solution

`scripts/install.sh` installs `sdc` to `~/.local/bin/sdc` (local) or
`/usr/local/bin/sdc` (`--global`), and `--check` verifies prerequisites.
Skill step files are migrated from `python3 .../scripts/*.py` to `sdc ...`.

#### Main User Flow

1. Maintainer runs `bash scripts/install.sh --check` to verify prerequisites.
2. Maintainer runs `bash scripts/install.sh` to install locally.
3. Skill references are updated to call `sdc` subcommands.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](PRD.md) |
| Backlog | What is true now, with evidence | [modules/cli/BACKLOG.md](modules/cli/BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](ARCHITECTURE.md) |