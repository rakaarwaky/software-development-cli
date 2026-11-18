# FRD — Plan Validator

## Feature Overview

```text
[Surface] --> [AgentPlanner] --> [CapabilitiesParsePrPlan / CapabilitiesValidateDag / CapabilitiesComputeExecution]
[Surface] --> [shared/src/planner/taxonomy_planner_request] (request/response VOs)
[AgentPlanner] --> [IPlanAggregate] (contract)
[Capabilities*] --> [IPlan*Protocol] (contract)
```

The **Plan Validator** feature parses the `## PR Plan` section of a design document, validates the PR dependency DAG, computes level assignments and final merge order, and returns a JSON report. The feature exposes one caller-observable action: `validate`, which reads a design document path, runs parse → validate → compute in sequence, and reports success or failure with structured errors.

## Functional Requirements

### FR-PLAN-001: Parse PR Plan

**Description:**
The feature shall extract all PR entries from the `## PR Plan` section of a design document. Each entry carries an ID, title, affected files/components, dependencies, and description. The feature rejects documents that lack a `## PR Plan` section or that contain no PR entries.

#### Business Logic
- The feature shall locate the `## PR Plan` section heading and read until the next `## ` heading or end of document.
- Fenced code blocks (``` or ~~~) shall be stripped before parsing so headings inside code examples are ignored.
- Each PR entry shall match the pattern `### PR <id>: <title>` and carry a `<id>` that becomes the PR's canonical identifier.
- Each entry body shall support bullets: `Files/components affected`, `Dependencies`, and `Description`.
- Dependencies shall be parsed from strings like `PR 0a, PR 1` into canonical `pr-<id>` identifiers.
- The feature shall return all parsed entries and any parse errors collected from dependency format mismatches.

#### Edge Cases
- If no `## PR Plan` section exists, the feature shall return a parse error with exit code `4` (`PlanValidationError`).
- If the section exists but contains no PR entries, the feature shall return a parse error.
- If a dependency string uses an unrecognized format (expected `PR <id>`), the feature shall record that as a parse error but continue parsing other entries.
- If the design document file does not exist, the feature shall return `PlanUsageError` with exit code `2`.
- If the design document file cannot be read due to permission errors, the feature shall return `PlanUsageError` with exit code `2`.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | Design document path; source: CLI argument `<design-doc-path>` |
| **Output** | Parsed PR entry list (internal VO) or parse error list |
| **Protocol** | `IPlanParseProtocol` |
| **Method** | `parse_plan(plan_text)` |
| **Event** | none |
| **Error** | `PlanValidationError` when no PR Plan section or no PR entries found |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Design document has `## PR Plan` with 3 valid PR entries | Call parse | 3 entries are returned with IDs, titles, files, dependencies, and descriptions |
| Design document has no `## PR Plan` section | Call parse | Parse error: "No '## PR Plan' section found in the document"; exit code `4` |
| Design document has `## PR Plan` but no PR entries | Call parse | Parse error: "No PR entries found in the PR Plan section"; exit code `4` |
| Dependency string uses unrecognized format | Call parse | Parse error recorded for that entry; other entries still parsed |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Parse latency (p95) | < 50ms |
| Parse accuracy (entries correctly extracted) | 100% |

### FR-PLAN-002: Validate DAG

**Description:**
The feature shall validate the PR dependency DAG for duplicate IDs, invalid dependency references, and cycles. When the DAG is invalid, the feature shall return a list of human-readable error strings.

#### Business Logic
- Each PR ID shall be unique across all parsed entries; duplicate IDs shall be reported as errors.
- Each dependency reference shall point to an existing PR ID; references to non-existent PRs shall be reported as errors.
- The dependency graph shall contain no cycles; cycles shall be reported as errors with the cycle path.
- Cycle detection shall use Kahn's algorithm for topological sort; when not all nodes are visited, the remaining nodes shall be traced to report one cycle path.
- When all validations pass, the DAG is considered valid with no errors.

#### Edge Cases
- If a duplicate PR ID exists across two entries, the feature shall report `Duplicate PR ID: '<id>'`.
- If a dependency references a PR that does not exist, the feature shall report the dependency and the entry it belongs to.
- If the DAG contains a cycle, the feature shall report `Cycle detected: <path>`.
- If the DAG is acyclic and all references are valid, no errors shall be returned.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | Parsed PR entry list; source: output of FR-PLAN-001 |
| **Output** | List of error strings (empty when valid) |
| **Protocol** | `IPlanValidateProtocol` |
| **Method** | `validate_dag(entries)` |
| **Event** | none |
| **Error** | `PlanValidationError` with all collected error strings when validation fails |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| Two PR entries share the same ID | Call validate | Error `Duplicate PR ID: '<id>'` is returned |
| Entry A depends on non-existent PR 99 | Call validate | Error referencing PR 99 in Entry A is returned |
| PR A depends on PR B, PR B depends on PR A | Call validate | Error `Cycle detected: pr-a -> pr-b -> pr-a` is returned |
| All dependencies are valid and acyclic | Call validate | Empty error list; DAG is valid |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Validation latency (p95) | < 50ms |
| Duplicate detection rate | 100% |
| Cycle detection rate | 100% |

### FR-PLAN-003: Compute Execution Plan

**Description:**
The feature shall compute level assignments, maximum parallelism, and a linearised merge order for a validated DAG. Level 0 is assigned to PRs with no dependencies; each subsequent level is one more than the maximum level of its dependencies.

#### Business Logic
- Level assignments shall be computed using Kahn's algorithm: each PR's level is `1 + max(level of its dependencies)`, with level 0 for PRs with no dependencies.
- The total number of levels shall be `max(level) + 1` when entries exist, or `0` when no entries exist.
- Maximum parallelism shall be the largest count of PRs at any single level.
- The linearised merge order shall flatten levels in ascending order; within each level, PRs shall be sorted by numeric ID first, then lexicographically.
- The return payload shall include `levels`, `max_parallelism`, `linearized_order`, and `level_assignments`.

#### Edge Cases
- When no entries exist, levels shall be `0` and max parallelism shall be `0`.
- When all PRs have no dependencies, all shall be at level 0 and max parallelism shall equal the total entry count.
- When PRs form a chain (A → B → C), levels shall be 0, 1, 2 and max parallelism shall be `1`.
- Level assignments shall be deterministic: same DAG always produces the same order.

#### Technical Specification
| Aspect | Detail |
|--------|--------|
| **Input** | Validated PR entry list; source: output of FR-PLAN-002 |
| **Output** | `{levels, max_parallelism, linearized_order, level_assignments}` |
| **Protocol** | `IPlanComputeProtocol` |
| **Method** | `compute_levels(entries)` |
| **Event** | none |
| **Error** | none (only called on valid DAG) |

#### Test
| Context | When Action | Then Observable Result |
|---------|-------------|------------------------|
| PRs A(no dep), B(depends on A), C(depends on B) | Call compute | Levels: A=0, B=1, C=2; max parallelism = 1 |
| PRs A(no dep), B(no dep), C(no dep) | Call compute | Levels: all 0; max parallelism = 3; order sorted numerically |
| No entries exist | Call compute | levels=0, max_parallelism=0, empty order |
| PRs at same level with mixed numeric/alpha IDs | Call compute | Order within level: numeric IDs first, then lexicographic |

#### Metric
| Target Metric | Value |
|---------------|-------|
| Compute latency (p95) | < 50ms |
| Level assignment determinism | 100% (same DAG → same result) |

## Public Interface

| Aspect     | Detail            |
|------------|-------------------|
| Agent      | `AgentPlanner`    |
| Aggregate  | `IPlanAggregate`  |
| Method     | `execute(request)` |
| Request    | `PlanRequest`     |
| Response   | `PlanResult`      |

## Reference

| Artifact     | Purpose                                         | Link |
|--------------|-------------------------------------------------|------|
| PRD          | Business goals, user stories, and scope         | [PRD.md](../../PRD.md) |
| Backlog      | Task tracking, epics, and implementation status | [BACKLOG.md](BACKLOG.md) |
| Roadmap      | Timeline, phasing, and dependencies             | [ROADMAP.md](../../ROADMAP.md) |
| Architecture | System boundaries, tech stack, and infra        | [ARCHITECTURE.md](../../ARCHITECTURE.md) |