# BACKLOG — CLI Surface

## Backlog

| ID | Status | Description | Priority |
|----|--------|-------------|----------|
| BL-CLI-001 | Done | Subcommand dispatch (host/memory/validate-plan) | P0 |
| BL-CLI-002 | Done | Host setup/cleanup via IHostAggregate | P0 |
| BL-CLI-003 | Done | Memory path/read/snapshot/update via IMemoryAggregate | P0 |
| BL-CLI-004 | Done | Validate-plan via IPlanAggregate | P0 |
| BL-CLI-005 | Done | Capability injection via set_capabilities | P0 |
| BL-CLI-006 | Todo | Add --help text for each subcommand | P2 |
| BL-CLI-007 | Todo | Add shell completion support | P3 |

## Done

- All core subcommands implemented and tested end-to-end
- AES contract compliance (no surface→capabilities direct imports)
- Capability injection pattern via root entry point

## Next

- Add shell completion
- Add --help text refinement