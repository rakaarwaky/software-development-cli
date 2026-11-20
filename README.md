# README — software-development-cli (`sdc`)

## Project Overview

`sdc` is a single stdlib-only Python CLI that consolidates the helper scripts
used by the `software-development` skills (`implement`, `planner`, `execute-plan`)
into one binary. It replaces the per-skill `scripts/host.py`,
`scripts/memory.py`, and `scripts/validate-plan.py` calls with a uniform
`sdc <subcommand>` surface, so skill step files stay thin and consistent.

## Prerequisites

- Python 3.9 or newer
- `uv` (Python package manager), confirmed with `uv --version`
- `bash` (for `scripts/install.sh`)
- `lint-arwaky-cli` and `mypy` for the quality gates (CI installs them; local runs need them on `PATH`)

## Quick Start

| Step | Action | Command |
|------|--------|---------|
| 1 | Verify prerequisites | `bash scripts/install.sh --check` |
| 2 | Install | `bash scripts/install.sh` (local XDG `~/.local/bin/sdc`) or `bash scripts/install.sh --global` (system-wide, needs sudo) |
| 3 | Host setup | `sdc host setup --subdir implement` |
| 4 | Memory path | `sdc memory path` |
| 5 | Memory update | `echo '{"patterns":[...]}' \| sdc memory update` |
| 6 | Memory top | `sdc memory top [--n N] [--category NAME]` |
| 7 | Validate plan | `sdc validate-plan <plan-doc-path>` |
| 8 | Pool grok | `sdc pool grok <session-id> [--wait]` |

### `sdc host <setup|cleanup>`

- `setup --subdir <implement|plan|execute>`: Creates `~/.agents/develop/<reponame>/<subdir>/` and prints JSON `{python, scratch_dir, run_id}`.
- `cleanup <paths...>`: Unlinks each path; missing paths are skipped.

### `sdc memory <path|read|update|top>`

- `path`: Print the memory file path for this workspace.
- `read`: Print the memory file contents (empty if missing).
- `update [--file <path>]`: Merge a JSON spec from stdin (or `--file`) into the memory file under an exclusive lock. The spec accepts `patterns` and an optional `run` object; `run.workflow` records the originating skill (`impl`/`exec`/`plan`/`grill`) as a `- **Workflow**:` body line.
- `top [--n N] [--category NAME]`: Print the top N common issue patterns as JSON (`patterns` sorted count-desc, `total`, `exists`), optionally filtered by category (case-insensitive). Read-only.

### `sdc validate-plan <plan-doc-path>`

Validates the `## PR Plan` section of a plan document: parses PR entries, validates the dependency DAG (unique IDs, valid references, no cycles), computes level assignments, and reports max parallelism as JSON.

### `sdc pool grok <session-id> [--wait]`

Polls a Grok Build session running in an Orca terminal and detects completion. Reads the rendered terminal screen with `orca terminal read --screen --json` (a full-screen TUI renders to the screen, not the PTY stream) and paces with `orca terminal wait --for tui-idle`.

- `<session-id>`: the Orca terminal handle of the running Grok session.
- `--wait`: block until completion, failure, or deadline (default: single non-blocking probe).
- `--deadline-hours` (default 2): wait-mode polling deadline.
- `--wait-ms` (default 15000): per-cycle `tui-idle` wait timeout.
- `--idle-confirm` (default 2): consecutive idle+final-report cycles before declaring done.
- `--sentinel` (default `EXECUTE_PLAN_COMPLETE`): completion sentinel to look for on screen.
- `--tail` (default 50): number of trailing screen lines to include in the result.
- `--orca`: override the Orca CLI executable.

Prints JSON `{session, status, sentinel, final_report, terminal_status, timed_out, cycles, cli_errors, tail}` to stdout. `status` is `done`/`running`/`failed`/`unknown`. Exit codes: `0` = done or running, `1` = failed/unknown/unwired, `3` = wait deadline exceeded. The orca CLI resolves via `--orca` → `ORCA_CLI_COMMAND` → `ORCA` → `orca-ide`/`orca` on `PATH`.

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | What sdc does and why | [PRD.md](PRD.md) |
| Roadmap | What ships next, in order | [ROADMAP.md](ROADMAP.md) |
| Architecture | Layer contract and linter rules | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Agent guide | How to work safely in this repo | [AGENTS.md](AGENTS.md) |
| Contributing | Branch, commit, and PR conventions | [CONTRIBUTING.md](CONTRIBUTING.md) |