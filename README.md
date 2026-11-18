# software-development-cli (`sdc`)

`sdc` is the single binary that consolidates the helper scripts used by the
`software-development` skills (`implement`, `design`, `execute-plan`) into one
stdlib-only Python CLI.

## Quick Start

| Step | Command |
|------|---------|
| Install | `bash scripts/install.sh` |
| Host setup | `sdc host setup --subdir implement` |
| Memory path | `sdc memory path` |
| Memory snapshot | `sdc memory snapshot` |
| Memory update | `echo '{"patterns":[...]}' \| sdc memory update` |
| Validate plan | `sdc validate-plan <design-doc-path>` |

## Subcommands

### `sdc host <setup|cleanup>`

- `setup --subdir <implement|plan|execute>`: Creates `~/.agents/develop/<reponame>/<subdir>/` and prints JSON `{python, scratch_dir, run_id}`.
- `cleanup <paths...>`: Unlinks each path; missing paths are skipped.

### `sdc memory <path|read|snapshot|update>`

- `path`: Print the memory file path for this workspace.
- `read`: Print the memory file contents (empty if missing).
- `snapshot`: Print the parsed memory file as JSON.
- `update [--file <path>]`: Merge a JSON spec from stdin (or `--file`) into the memory file under an exclusive lock.

### `sdc validate-plan <design-doc-path>`

Validates the `## PR Plan` section of a design document: parses PR entries,
validates the dependency DAG (unique IDs, valid references, no cycles),
computes level assignments, and reports max parallelism as JSON.

## Installation

```bash
bash scripts/install.sh          # Local XDG install (~/.local/bin/sdc)
bash scripts/install.sh --global # System-wide (/usr/local/bin/sdc, requires sudo)
bash scripts/install.sh --check  # Verify prerequisites only
```

## AES Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the layer contract and import rules.

## Reference

- [AGENTS.md](AGENTS.md) — Operational guide for agents
- [CONTRIBUTING.md](CONTRIBUTING.md) — Branch, commit, and PR conventions
- [ARCHITECTURE.md](ARCHITECTURE.md) — Layer contract
- [ROADMAP.md](ROADMAP.md) — What ships next
- [PRD.md](PRD.md) — What the product does and why