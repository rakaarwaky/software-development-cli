# Plan: Full Memory Feature Implementation Across All 4 Skills

## Goal

Ensure all four software-development skills (`implement`, `execute-plan`, `planner`, `grill-me`) fully utilize the `sdc memory` capability by enforcing `run.workflow` provenance, integrating `sdc memory top` into retrieval flows, and adding validation/test coverage.

## Current Context / Assumptions

- The `sdc memory` CLI (`path|read|snapshot|update|top`) is implemented and tested (197 passed, 3 skipped, 0 linter violations).
- All four skills reference `sdc memory` in their step files, but currently:
  - `run.workflow` is a convention in documentation, not enforced by code.
  - `sdc memory top` was added to step files (P2) but not yet integrated into orchestrator code paths.
  - There is no test coverage verifying that each skill produces specs with the correct `run.workflow` prefix.
- The codebase has no existing Python orchestrator scripts for the skills — they are driven by markdown step files executed by LLM agents.

## Architecture / Proposed Approach

Since the skills are LLM-driven (not code-driven), "full implementation" means:
1. **Enforce `run.workflow` in code**: Add validation in `sdc memory update` to reject specs where `run.description` does not start with the expected workflow prefix (`impl:`, `exec:`, `plan:`, `grill:`).
2. **Integrate `sdc memory top` into retrieval**: Update each skill's retrieval step file to use `sdc memory top --n 10` instead of `sdc memory snapshot`, and parse the `patterns` field.
3. **Add integration tests**: Write tests that exercise each skill's memory spec format and verify the `run.workflow` field is present and correct.

## Step-by-Step Tasks

### Task 1: Add `run.workflow` validation to `sdc memory update` capability

**File:** `modules/memory/src/capabilities_memory_writer.py`

**Action:** Add validation that checks `run.description` starts with a recognized workflow prefix. Reject with `SpecError` (exit code 4) if missing.

**Implementation:**

```python
# In capabilities_memory_writer.py, inside the update() method,
# after parsing the spec but before merging:

VALID_WORKFLOW_PREFIXES = ("impl: ", "exec: ", "plan: ", "grill: ")

def _validate_workflow(run_spec: dict) -> None:
    """Reject specs whose run.description lacks a recognized workflow prefix."""
    if not run_spec:
        return  # no run entry — allowed (patterns-only update)
    desc = run_spec.get("description", "")
    if not isinstance(desc, str):
        raise SpecError('"run.description" must be a string')
    if not any(desc.startswith(p) for p in VALID_WORKFLOW_PREFIXES):
        raise SpecError(
            f'"run.description" must start with one of {VALID_WORKFLOW_PREFIXES}; '
            f"got: {desc[:50]!r}"
        )
```

Call `_validate_workflow(run_spec)` inside `update()` before writing.

**Verification:**
```bash
cd /home/raka/.agents/skills/software-development/tools
echo '{"run":{"description":"missing prefix"}}' | python3 -m sdc memory update
# Expected: exit code 4, stderr: 'run.description must start with one of ...'

echo '{"run":{"description":"impl: valid prefix"}}' | python3 -m sdc memory update
# Expected: exit code 0 (or 3 if lock contention, but not 4)
```

### Task 2: Add unit tests for `run.workflow` validation

**File:** `modules/memory/tests/unit_capabilities_memory_writer.py`

**Action:** Add test cases for the new validation.

**Implementation:**

```python
def test_run_without_workflow_prefix_raises_spec_error(self, isolated_home, git_repo):
    writer = CapabilitiesWriter()
    with pytest.raises(SpecError) as exc_info:
        writer.update({"run": {"description": "no prefix here"}})
    assert exc_info.value.exit_code == 4
    assert "must start with one of" in str(exc_info.value)

def test_run_with_valid_impl_prefix_succeeds(self, isolated_home, git_repo):
    writer = CapabilitiesWriter()
    res = writer.update({"run": {"description": "impl: valid workflow"}})
    assert res.existed_before is False  # first write

def test_run_with_valid_exec_prefix_succeeds(self, isolated_home, git_repo):
    writer = CapabilitiesWriter()
    res = writer.update({"run": {"description": "exec: valid workflow"}})
    assert res.existed_before is False

def test_run_with_valid_plan_prefix_succeeds(self, isolated_home, git_repo):
    writer = CapabilitiesWriter()
    res = writer.update({"run": {"description": "plan: valid workflow"}})
    assert res.existed_before is False

def test_run_with_valid_grill_prefix_succeeds(self, isolated_home, git_repo):
    writer = CapabilitiesWriter()
    res = writer.update({"run": {"description": "grill: valid workflow"}})
    assert res.existed_before is False

def test_run_without_description_is_allowed(self, isolated_home, git_repo):
    """Patterns-only update (no run entry) is allowed."""
    writer = CapabilitiesWriter()
    res = writer.update({"patterns": [{"category": "Testing", "description": "x"}]})
    assert res.existed_before is False
```

**Verification:**
```bash
cd /home/raka/.agents/skills/software-development/tools
PYTHONPATH=modules .venv/bin/python -m pytest modules/memory/tests/unit_capabilities_memory_writer.py -q
# Expected: all tests pass
```

### Task 3: Update `implement` skill retrieval step to use `sdc memory top`

**File:** `/home/raka/.agents/skills/software-development/implement/references/grok/step-2-memory.md`

**Current state:** Uses `sdc memory snapshot` and parses `common_issues`.

**Action:** Change to `sdc memory top --n 10` and parse the `patterns` field.

**Implementation:**

Replace the retrieval section with:

```markdown
1. Run `cd <worktree_path> && sdc memory top --n 10` via `run_terminal_command` and capture stdout. The `top` subcommand is the cheap read-only briefing query — it returns the count-desc top-10 patterns without parsing the full snapshot. The helper prints structured JSON:

   ```json
   {
     "patterns": [
       {"category": "Error Handling", "description": "Missing null check", "count": 5},
       ...
     ],
     "total": 12,
     "exists": true
   }
   ```

   Parse the JSON and store the `patterns` list as `existing_patterns_snapshot` (used in Step 8b). Store the boolean `exists` as `memory_existed_before` (used in the Final Report to decide between "file created" and "file updated" wording). The `total` field is the full pattern count (before the `--n 10` truncation); the orchestrator does not consume it beyond the briefing.
```

**Verification:**
```bash
# Verify the file was updated:
grep -n "sdc memory top" /home/raka/.agents/skills/software-development/implement/references/grok/step-2-memory.md
# Expected: at least one match showing "sdc memory top --n 10"
```

### Task 4: Update `execute-plan` skill retrieval step to use `sdc memory top`

**File:** `/home/raka/.agents/skills/software-development/execute-plan/references/grok/step-1-memory-retrieval.md`

**Current state:** Uses `sdc memory snapshot` and parses `common_issues`.

**Action:** Change to `sdc memory top --n 10` and parse the `patterns` field.

**Implementation:**

Replace the retrieval section with:

```markdown
1. Run `sdc memory top --n 10` via `run_terminal_command` and capture stdout. The helper prints structured JSON:

   ```json
   {
     "patterns": [
       {"category": "Error Handling", "description": "Missing null check", "count": 5}
     ],
     "total": 12,
     "exists": true
   }
   ```

   Store the `patterns` list as `existing_patterns_snapshot`. Store the boolean `exists` as `memory_existed_before`.
```

**Verification:**
```bash
grep -n "sdc memory top" /home/raka/.agents/skills/software-development/execute-plan/references/grok/step-1-memory-retrieval.md
# Expected: at least one match
```

### Task 5: Update `planner` skill retrieval step to use `sdc memory top`

**File:** `/home/raka/.agents/skills/software-development/planner/references/grok/step-0-setup.md`

**Current state:** Already updated in P2 to use `sdc memory top --n 10`.

**Action:** Verify the file already uses `sdc memory top` and parse the `patterns` field.

**Verification:**
```bash
grep -n "sdc memory top" /home/raka/.agents/skills/software-development/planner/references/grok/step-0-setup.md
# Expected: at least one match
```

### Task 6: Update `grill-me` skill retrieval step to use `sdc memory top`

**File:** `/home/raka/.agents/skills/software-development/grill-me/references/grok/step-0-setup.md`

**Current state:** Already updated in P2 to use `sdc memory top --n 10`.

**Action:** Verify the file already uses `sdc memory top` and parse the `patterns` field.

**Verification:**
```bash
grep -n "sdc memory top" /home/raka/.agents/skills/software-development/grill-me/references/grok/step-0-setup.md
# Expected: at least one match
```

### Task 7: Add integration test for cross-skill memory specs

**File:** `modules/memory/tests/integration_memory.py`

**Action:** Add a test that verifies all four workflow prefixes are accepted by the `update` capability.

**Implementation:**

```python
def test_all_four_workflow_prefixes_accepted(self, isolated_home, git_repo):
    """All four workflow prefixes must be accepted by sdc memory update."""
    writer = CapabilitiesWriter()
    prefixes = ["impl: ", "exec: ", "plan: ", "grill: "]
    for prefix in prefixes:
        res = writer.update({"run": {"description": f"{prefix}test workflow"}})
        # Each should succeed (existed_before may be True after first)
        assert res is not None
```

**Verification:**
```bash
cd /home/raka/.agents/skills/software-development/tools
PYTHONPATH=modules .venv/bin/python -m pytest modules/memory/tests/integration_memory.py -q
# Expected: all tests pass
```

### Task 8: Run full test suite and linter

**Verification:**
```bash
cd /home/raka/.agents/skills/software-development/tools

# Run tests
PYTHONPATH=modules .venv/bin/python -m pytest modules/ -q -m "not dogfood"
# Expected: 197+ passed, 3+ skipped, 0 failed

# Run linter
lint-arwaky-cli scan modules
# Expected: Total: 0 violations
```

## Tests / Validation

| Test | Command | Expected Output |
|------|---------|-----------------|
| Workflow validation | `echo '{"run":{"description":"bad"}}' \| python3 -m sdc memory update` | Exit 4, stderr mentions "must start with one of" |
| Valid workflow prefix | `echo '{"run":{"description":"impl: ok"}}' \| python3 -m sdc memory update` | Exit 0 |
| Unit tests | `PYTHONPATH=modules .venv/bin/python -m pytest modules/memory/tests/unit_capabilities_memory_writer.py -q` | All pass |
| Integration tests | `PYTHONPATH=modules .venv/bin/python -m pytest modules/memory/tests/integration_memory.py -q` | All pass |
| Full suite | `PYTHONPATH=modules .venv/bin/python -m pytest modules/ -q -m "not dogfood"` | 197+ passed |
| Linter | `lint-arwaky-cli scan modules` | 0 violations |

## Risks, Tradeoffs, and Open Questions

| Risk | Mitigation |
|------|------------|
| Existing memory files may have specs without workflow prefixes | Validation only applies to new writes; old files are untouched |
| Agents may forget the prefix in `run.description` | Clear error message guides them to fix it |
| `sdc memory top` may not be available in older installations | Graceful degradation: if `top` fails, fall back to `snapshot` |
| Four skills must stay in lockstep | Integration test verifies all four prefixes are accepted |
| No Python orchestrator code exists for skills | This plan focuses on the `sdc memory` CLI and step-file documentation, which is what agents actually execute |

## Open Questions

1. **Should `sdc memory update` accept a `--workflow` flag** instead of requiring the prefix in `run.description`?
   - Pro: More explicit, less error-prone.
   - Con: Adds CLI surface area; current approach (prefix in description) is simpler and already documented.
   - Recommendation: Keep current approach. The prefix is part of the description convention and is self-documenting.

2. **Should there be a migration path for existing memory files that lack workflow prefixes?**
   - Current answer: No. Old entries are preserved as-is; only new entries require the prefix.

3. **Should `sdc memory top` be the default for all retrieval, or keep `snapshot` as fallback?**
   - Current answer: `top` is the primary retrieval command. `snapshot` remains available for debugging/full inspection. Step files already updated to use `top`.