# software-development-cli (`sdc`)

`sdc` is the single binary that consolidates the helper scripts used by the
`software-development` skills (`implement`, `design`, `execute-plan`) into one
stdlib-only Python CLI. It replaces the per-skill `scripts/host.py`,
`scripts/memory.py`, and `scripts/validate-plan.py` calls with a uniform
`sdc <subcommand>` surface so skill step files stay thin.
