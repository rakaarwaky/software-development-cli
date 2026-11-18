# CONTRIBUTING — software-development-cli

## Contribution Overview

Contribute changes that keep every `sdc` subcommand and flag in lockstep across `modules/`, `README.md`, `AGENTS.md`, and each feature's `FRD.md`. A change is ready to merge when it follows the AES layer contract, passes the local quality gates below, and lands as one feature per PR against `main`.

## Contribution Guidelines

- Edit only files under `modules/`; leave root docs (`README.md`, `AGENTS.md`, `ARCHITECTURE.md`) in sync when a flag or subcommand term changes.
- Keep stdlib-only Python 3.9+; do not add third-party runtime dependencies.
- Follow the AES 7-layer contract documented in `ARCHITECTURE.md`; new violations fail CI.
- Write or update tests alongside the code; the change is incomplete if the gates below do not pass.

### Quality Gates

| Gate | Command |
|------|---------|
| Unit tests | `python3 -m pytest modules/ -q -m "not dogfood"` |
| Module tests | `python3 -m pytest modules/ -q` |
| Type check | `python3 -m mypy modules/` |
| Arch scan | `lint-arwaky-cli scan modules` |

## Workflow

| Step | Action | Detail |
|------|--------|--------|
| 1 | Branch | `feature/<topic>` or `fix/<topic>` |
| 2 | Implement | Follow the FRD spec in the feature folder, write tests |
| 3 | Self-review | Run every Quality Gate locally; fix violations before pushing |
| 4 | Submit PR | Open against `main`, one feature per PR, describe what changed |
| 5 | Review | CI must pass: lint + tests (`ci.yml` jobs) |
| 6 | Merge | Squash-merge once required checks are green |

## Commit Convention

| Type | Usage | Example |
|------|-------|---------|
| `feat` | New feature | `feat(host): add subdir validation` |
| `fix` | Bug fix | `fix(memory): correct path resolution` |
| `refactor` | Code restructure | `refactor(planner): split DAG validator` |
| `docs` | Documentation only | `docs(readme): document memory subcommand` |
| `test` | Test additions | `test(cli): cover surface dispatch` |
| `chore` | Build/CI/tooling | `chore: bump uv lockfile` |

## Reference

| Artifact | Purpose | Link |
|----------|---------|------|
| PRD | What sdc does and why | [PRD.md](PRD.md) |
| Architecture | Layer contract and linter rules | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Agent guide | How to work safely in this repo | [AGENTS.md](AGENTS.md) |
| Roadmap | What ships next, in order | [ROADMAP.md](ROADMAP.md) |