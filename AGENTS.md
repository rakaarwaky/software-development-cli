---
trigger: always
description: "AGENTS.md operational guide for software-development-cli (sdc)."
---

# AGENTS — software-development-cli

## Agent Overview

`sdc` is the single binary that consolidates the helper scripts used by the
`software-development` skills (`implement`, `planner`, `execute-plan`) into one
stdlib-only Python CLI. It replaces the per-skill `scripts/host.py`,
`scripts/memory.py`, and `scripts/validate-plan.py` calls with a uniform
`sdc <subcommand>` surface so skill step files stay thin. Agents generating
code, docs, or suggestions must only edit files under `modules/` and must
keep every flag and subcommand term in lockstep across `README.md`,
`AGENTS.md`, and the FRD.md files in each feature folder.

## Runtime

| Aspect          | Detail                                          |
|-----------------|-------------------------------------------------|
| Language        | Python 3.9+                                     |
| Environment     | `uv` (Python package manager)                   |
| Artifacts       | `modules/` AES layers, `scripts/install.sh`     |
| Package Manager | uv                                              |
| Version Probe   | `uv --version`                                  |
| Setup           | `bash scripts/install.sh --check`               |
| Activation      | `source .venv/bin/activate`                     |

## Project Structure

```text
.
├── PRD.md                      # What sdc does and why
├── ROADMAP.md                  # What ships next, in order
├── README.md                   # How to use/run
├── AGENTS.md                   # This file — how to work here safely
├── CONTRIBUTING.md             # Branch, commit, and PR conventions
├── ARCHITECTURE.md             # Layer contract and linter rule catalog
├── scripts/
│   └── install.sh              # XDG bin installer
└── modules/                    # AES layer implementation
    ├── cli/                    # Surface layer (CLI dispatch)
    │   ├── src/                # surface_sdc_command
    │   ├── FRD.md              # Feature requirements
    │   └── BACKLOG.md          # Feature backlog
    ├── planner/                # PR Plan validator feature
    │   ├── src/                # capabilities_plan_validator
    │   ├── FRD.md
    │   └── BACKLOG.md
    ├── memory/                 # Memory store feature
    │   ├── src/                # capabilities_memory_store
    │   ├── FRD.md
    │   └── BACKLOG.md
    ├── host/                   # Host helper feature
    │   ├── src/                # capabilities_host_helper
    │   ├── FRD.md
    │   └── BACKLOG.md
    ├── pool/                   # Agent-session pooler (Grok Build)
    │   ├── src/                # agent + capabilities_pool_grok
    │   ├── FRD.md
    │   └── BACKLOG.md
    ├── shared/                 # Shared kernel
    │   ├── src/common/         # taxonomy + utility
    │   ├── src/host/           # host contracts + taxonomy
    │   ├── src/memory/         # memory contracts + taxonomy
    │   ├── src/pool/           # pool contracts + taxonomy
    │   ├── src/planner/        # planner contracts + taxonomy
    │   ├── DATA.md
    │   └── BACKLOG.md
    └── root_sdc_entry.py       # Root entry (wires capabilities → surface)
```

## Commands

| Category    | Command                              | Scope      | CI Gate              |
|-------------|--------------------------------------|------------|----------------------|
| Test (all)  | `python3 -m pytest modules/ -q`      | All        | ci.yml: Module tests |
| Test (unit) | `python3 -m pytest modules/ -q -m "not dogfood"` | One unit | ci.yml: Skills and shared tests |
| Test (file) | `python3 -m pytest <path-to-test-file> -q` | One file | ci.yml: Module tests |
| Lint        | `lint-arwaky-cli scan modules`       | All        | ci.yml: Architecture scan |
| Type Check  | `python3 -m mypy modules/`           | All        | ci.yml: Python compile check |
| Arch Scan   | `lint-arwaky-cli scan modules`       | All        | ci.yml: Architecture scan |

## Reference

| Artifact     | Purpose                                    | Link |
|--------------|--------------------------------------------|------|
| README       | What the tool does, every command, install | [README.md](README.md) |
| CONTRIBUTING | Branch, commit, and PR conventions         | [CONTRIBUTING.md](CONTRIBUTING.md) |
| ARCHITECTURE | Layer contract for every crate             | [ARCHITECTURE.md](ARCHITECTURE.md) |
| ROADMAP      | What ships next, in order                  | [ROADMAP.md](ROADMAP.md) |
| PRD          | What the product does and why              | [PRD.md](PRD.md) |