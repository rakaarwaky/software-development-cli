# ARCHITECTURE — software-development-cli

## Overview

`sdc` follows the Agentic Engineering System (AES) 7-layer architecture.
Files are grouped by feature, with layers as filenames, not directories.
The import matrix enforces bottom-up dependencies: taxonomy → contract →
utility → capabilities → agent → surface → root.

## Layer Map

| Layer | Location | Files |
|-------|----------|-------|
| Taxonomy | `modules/shared/src/*/taxonomy_*.py` | Constants, errors, VOs, request/response |
| Contract | `modules/shared/src/*/contract_*.py` | ABC protocols + aggregates |
| Utility | `modules/shared/src/common/utility_*.py` | Stateless helpers |
| Capabilities | `modules/*/src/capabilities_*.py` | Concrete implementations |
| Surface | `modules/cli/src/surface_*.py` | CLI dispatch |
| Root | `modules/root_sdc_entry.py` | Capability wiring |

## Feature Folders

| Folder | Owns | Shared Subfolder |
|--------|------|------------------|
| `cli` | `capabilities_host_helper.py`, `surface_sdc_command.py` | `shared/src/host/` |
| `planner` | `capabilities_plan_validator.py` | `shared/src/planner/` |
| `memory` | `capabilities_memory_store.py` | `shared/src/memory/` |
| `host` | (capabilities live in `cli/`) | `shared/src/host/` |

## Import Rules

| Scope | Allowed | Forbidden |
|-------|---------|-----------|
| taxonomy | taxonomy only | agent, surface, contract, utility, capabilities, root |
| contract | taxonomy, contract | agent, surface, capabilities, root |
| utility | taxonomy | agent, surface, contract, capabilities, root, utility |
| capabilities | taxonomy, contract, utility | surface, agent, capabilities, root |
| surface | taxonomy, contract(aggregate), utility | agent, capabilities, contract(protocol), root |
| root | all layers | — |

## Exit Code Contract

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Classified runtime failure |
| 2 | Usage error |
| 3 | Memory lock timeout |
| 4 | Memory spec error |