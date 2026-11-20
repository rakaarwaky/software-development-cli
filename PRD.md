# PRD — software-development-cli

## Project Overview

    [Skills] --> [sdc CLI] --> [Host / Memory / Planner capabilities]

**software-development-cli (`sdc`)** is a project that consolidates the helper
scripts used by the `software-development` skills (`implement`, `planner`,
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

- `sdc host setup|cleanup` for per-repo artifact directories, implemented on the AES 7-layer architecture and shipped through the XDG installer.
- `sdc memory path|read|update|top` for per-repo memory files, implemented on the AES 7-layer architecture and shipped through the XDG installer.
- `sdc validate-plan` for PR-plan DAG validation, implemented on the AES 7-layer architecture and shipped through the XDG installer.
- `sdc pool grok <session-id>` for polling a Grok Build session until completion, implemented on the AES 7-layer architecture and shipped through the XDG installer.
- `sdc` CLI surface dispatching to host, memory, planner, and pool contracts, shipped through `scripts/install.sh` to `~/.local/bin/sdc`.

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
| Skill author | to call `sdc host|memory|validate-plan` with flags, installed via `scripts/install.sh` and built on the AES 7-layer architecture | skill step files stay thin | P0 |

#### Proposed Solution

A single `sdc` entry point parses argv, dispatches each subcommand to its
contract aggregate, and renders JSON output to stdout with exit codes 0/1/2/3/4.
The `modules/` tree follows the AES 7-layer architecture wired from a root
entry, CI runs `lint-arwaky-cli scan modules`, `pytest`, and `mypy`, and
`scripts/install.sh` installs `sdc` to `~/.local/bin/sdc`.

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

`sdc memory path|read|update|top` manages a per-repo memory file under
`~/.agents/develop/<reponame>/memory/`. `update` merges a JSON spec from stdin
(or `--file`) into the file under an exclusive lock, skipping lines that
already exist.

#### Main User Flow

1. Skill step calls `sdc memory path` to learn where memory lives.
2. Skill step calls `sdc memory read` or `sdc memory top` to load it.
3. Skill step pipes a JSON spec into `sdc memory update` to merge new notes.
4. Skill step calls `sdc memory top` to pull the most-recurring patterns without parsing the whole file.

### PR-SDC-004: Planner Helper

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | to validate a PR-plan DAG before execution | execution runs only acyclic, dependency-complete plans | P1 |

#### Proposed Solution

`sdc validate-plan <plan-doc-path>` parses the `## PR Plan` section of a
plan document, validates the dependency DAG (unique IDs, valid references,
no cycles), computes level assignments, and reports max parallelism as JSON.

#### Main User Flow

1. Author saves a plan document with a `## PR Plan` section.
2. Author runs `sdc validate-plan <plan-doc-path>`.
3. `sdc` prints a JSON report with `valid`, `pr_count`, `levels`, `max_parallelism`, and any errors.

### PR-SDC-005: Pool Helper

#### User Stories

| As a | I want | So that | Priority |
|------|--------|---------|----------|
| Skill author | to call `sdc pool grok <session-id> [--wait]` | I can standardize how I poll a Grok Build session until it completes | P1 |

#### Proposed Solution

`sdc pool grok <session-id>` polls the rendered screen of an Orca terminal running a Grok Build TUI session and detects completion via a configurable sentinel (default `EXECUTE_PLAN_COMPLETE`) or a final-report shape on an idle screen. With `--wait` it blocks until completion, failure, or deadline (default 2h). Output is JSON to stdout with exit codes 0/1/3.

#### Main User Flow

1. Author runs `sdc pool grok <session-id>` to probe once.
2. Author runs `sdc pool grok --wait <session-id>` to block until the session completes.
3. `sdc` prints a JSON report with `session`, `status`, `sentinel`, `final_report`, `terminal_status`, `timed_out`, `cycles`, `cli_errors`, `tail`.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | Business goals, user stories, and scope | [PRD.md](PRD.md) |
| Backlog | What is true now, with evidence | [modules/cli/BACKLOG.md](modules/cli/BACKLOG.md) |
| Roadmap | Timeline, phasing, and dependencies | [ROADMAP.md](ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra | [ARCHITECTURE.md](ARCHITECTURE.md) |