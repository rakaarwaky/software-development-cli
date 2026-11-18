"""PR Plan validator capability (AES capabilities layer).

Ported from ``skills/software-development/execute-plan/scripts/validate-plan.py``.

Parses the ``## PR Plan`` section of a design document, extracts PR
entries from ``### PR N:`` headings, validates the dependency DAG
(unique IDs, valid references, no cycles), computes level assignments,
linearises for final branch merge order, and reports max parallelism.

Implements the ``IPlanAggregate`` contract.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque
from pathlib import Path

from shared.src.common.taxonomy_sdc_error import (
    PlanUsageError,
    PlanValidationError,
)
from shared.src.common.taxonomy_sdc_vo import PlanReport, PrEntry
from shared.src.planner.contract_planner_aggregate import IPlanAggregate
from shared.src.planner.taxonomy_planner_request import PlanRequest, PlanResult


class PlanValidator(IPlanAggregate):
    """Concrete PR Plan validator implementing ``IPlanAggregate``."""

    def execute(self, request: PlanRequest) -> PlanResult:
        if request.action == "validate":
            report = validate_plan_file(request.path)
            return PlanResult(
                valid=report.valid,
                pr_count=report.pr_count,
                levels=report.levels,
                max_parallelism=report.max_parallelism,
                linearized_order=report.linearized_order,
                level_assignments=report.level_assignments,
                errors=report.errors,
            )
        raise PlanUsageError(
            f"planner: unknown action {request.action!r}; expected 'validate'"
        )


# ─── Block 1: Module Declaration ───────────────────────────────────────

# ─── Parsing ──────────────────────────────────────────────────────────


def _strip_fenced_code_blocks(content: str) -> str:
    """Remove fenced code blocks so headings inside examples are ignored."""
    flags = re.MULTILINE | re.DOTALL
    content = re.sub(r"^\s*```[^\n]*\n.*?^\s*```\s*$", "", content, flags=flags)
    return re.sub(r"^\s*~~~[^\n]*\n.*?^\s*~~~\s*$", "", content, flags=flags)


def parse_pr_plan(content: str) -> tuple[list[PrEntry] | None, list[str]]:
    """Parse the ``## PR Plan`` section.

    Returns ``(entries, [])`` on success or ``(None, [error, ...])`` on failure.
    """
    stripped = _strip_fenced_code_blocks(content)
    heading = re.search(r"^## PR Plan\s*$", stripped, re.MULTILINE)
    if heading is None:
        return None, ["No '## PR Plan' section found in the document"]

    start = heading.end()
    next_section = re.search(r"^## (?!PR Plan\s*$)", stripped[start:], re.MULTILINE)
    section = stripped[start : start + next_section.start()] if next_section else stripped[start:]

    pr_re = re.compile(r"^###\s+PR\s+(\S+?):\s*(.+)$", re.MULTILINE)
    matches = list(pr_re.finditer(section))

    if not matches:
        return None, ["No PR entries found in the PR Plan section"]

    entries: list[PrEntry] = []
    parse_errors: list[str] = []
    for i, m in enumerate(matches):
        pr_num = m.group(1)
        title = m.group(2).strip()

        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(section)
        body = section[body_start:body_end]

        files_raw = _extract_field(body, "Files/components affected")
        deps_raw = _extract_field(body, "Dependencies")
        description = _extract_field(body, "Description") or ""

        files = [f.strip() for f in files_raw.split(",") if f.strip()] if files_raw else []
        dependencies, dep_errors = _parse_dependencies(deps_raw, f"PR {pr_num}")
        parse_errors.extend(dep_errors)

        entries.append(
            PrEntry(
                id=f"pr-{pr_num.lower()}",
                number=pr_num,
                title=title,
                files=files,
                dependencies=dependencies,
                description=description,
            )
        )

    if parse_errors:
        return None, parse_errors
    return entries, []


def _extract_field(body: str, field_name: str) -> str | None:
    """Return the value of a ``- **FieldName:** value`` bullet, or None."""
    escaped = re.escape(field_name)
    pattern = re.compile(
        rf"^\s*[-*]\s+\**{escaped}:?\**:?\s*(.+(?:\n[ \t]+\S.*)*)",
        re.MULTILINE | re.IGNORECASE,
    )
    m = pattern.search(body)
    if m:
        return re.sub(r"\s*\n[ \t]+", " ", m.group(1)).strip()
    return None


def _parse_dependencies(deps_raw: str | None, pr_label: str) -> tuple[list[str], list[str]]:
    """Turn a dependency string like ``"PR 0a, PR 1"`` into ``(ids, errors)``."""
    if not deps_raw:
        return [], []
    stripped = deps_raw.strip()
    if stripped.lower() in ("none", "n/a", "-", ""):
        return [], []

    parts = [p.strip() for p in stripped.split(",")]
    deps: list[str] = []
    errors: list[str] = []
    for part in parts:
        if not part:
            continue
        m = re.match(r"PR\s+(\S+)", part, re.IGNORECASE)
        if m:
            deps.append(f"pr-{m.group(1).lower()}")
        else:
            errors.append(
                f"Unrecognized dependency format '{part}' in {pr_label} (expected 'PR <id>')"
            )
    return deps, errors


# ─── Block 2: Module Contract ──────────────────────────────────────────

# (Implemented inline in PlanValidator.execute above.)

# ─── Block 3: Module Helpers ───────────────────────────────────────────

# ─── Validation ───────────────────────────────────────────────────────


def validate_dag(entries: list[PrEntry]) -> list[str]:
    """Check unique IDs, valid dependency references, and no cycles."""
    errors: list[str] = []

    seen: set[str] = set()
    for entry in entries:
        if entry.id in seen:
            errors.append(f"Duplicate PR ID: '{entry.id}'")
        seen.add(entry.id)

    for entry in entries:
        for dep in entry.dependencies:
            if dep not in seen:
                dep_label = dep.replace("pr-", "PR ", 1)
                entry_label = entry.id.replace("pr-", "PR ", 1)
                errors.append(
                    f"Dependency '{dep_label}' in {entry_label} does not reference a valid PR ID"
                )

    if not errors:
        errors.extend(_detect_cycles(entries))

    return errors


def _detect_cycles(entries: list[PrEntry]) -> list[str]:
    """Kahn's algorithm for topological sort; returns cycle errors."""
    in_degree: dict[str, int] = {e.id: 0 for e in entries}
    children: dict[str, list[str]] = defaultdict(list)
    dep_map: dict[str, list[str]] = {e.id: e.dependencies for e in entries}

    for entry in entries:
        for dep in entry.dependencies:
            children[dep].append(entry.id)
            in_degree[entry.id] += 1

    queue: deque[str] = deque(eid for eid, deg in in_degree.items() if deg == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for child in children[node]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if visited == len(entries):
        return []

    unvisited = [e.id for e in entries if in_degree[e.id] > 0]
    cycle = _trace_cycle(dep_map, unvisited)
    if cycle:
        return [f"Cycle detected: {' -> '.join(cycle)}"]
    return [f"Cycle detected involving: {', '.join(sorted(unvisited))}"]


def _trace_cycle(dep_map: dict[str, list[str]], unvisited_ids: list[str]) -> list[str] | None:
    """Walk deps among *unvisited_ids* to report one cycle path."""
    unvisited = set(unvisited_ids)
    current = unvisited_ids[0]
    path = [current]
    visited_in_path = {current}

    while True:
        next_node = None
        for dep in dep_map.get(current, []):
            if dep in unvisited:
                next_node = dep
                break
        if next_node is None:
            break
        if next_node in visited_in_path:
            idx = path.index(next_node)
            return path[idx:] + [next_node]
        path.append(next_node)
        visited_in_path.add(next_node)
        current = next_node

    return None


# ─── DAG processing ───────────────────────────────────────────────────


def _pr_sort_key(pr_id: str) -> tuple[int, int, str]:
    """Sort key: numeric PR numbers first, then lexicographic."""
    suffix = pr_id.split("-", 1)[1] if "-" in pr_id else pr_id
    try:
        return (0, int(suffix), "")
    except ValueError:
        return (1, 0, suffix)


def compute_levels(entries: list[PrEntry]) -> dict[str, int]:
    """Return ``{pr_id: level}``; level 0 = no deps."""
    children: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = {e.id: 0 for e in entries}

    for e in entries:
        for dep in e.dependencies:
            children[dep].append(e.id)
            in_degree[e.id] += 1

    levels: dict[str, int] = {}
    queue: deque[str] = deque()
    for eid, deg in in_degree.items():
        if deg == 0:
            levels[eid] = 0
            queue.append(eid)

    while queue:
        node = queue.popleft()
        for child in children[node]:
            candidate = levels[node] + 1
            levels[child] = max(levels.get(child, 0), candidate)
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    return levels


def linearize(entries: list[PrEntry], levels: dict[str, int]) -> list[str]:
    """Flatten the DAG into final branch merge order (stable within levels)."""
    by_level: dict[int, list[str]] = defaultdict(list)
    for e in entries:
        by_level[levels[e.id]].append(e.id)

    order: list[str] = []
    for lv in sorted(by_level):
        order.extend(sorted(by_level[lv], key=_pr_sort_key))
    return order


# ─── Public entry point ───────────────────────────────────────────────


def validate_plan_file(path: str) -> PlanReport:
    """Validate the PR Plan DAG in the design document at ``path``.

    Raises ``PlanUsageError`` when the file is missing or unreadable.
    Raises ``PlanValidationError`` when the DAG is invalid.
    Returns a ``PlanReport`` on success.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise PlanUsageError(f"File not found: {path}")
    except OSError as exc:
        raise PlanUsageError(f"Cannot read file {path}: {exc}")

    entries, parse_errors = parse_pr_plan(content)
    if parse_errors:
        raise PlanValidationError("\n".join(parse_errors))

    errors = validate_dag(entries)
    if errors:
        raise PlanValidationError("\n".join(errors))

    levels = compute_levels(entries)
    order = linearize(entries, levels)

    num_levels = max(levels.values()) + 1 if levels else 0
    counts: dict[int, int] = defaultdict(int)
    for lv in levels.values():
        counts[lv] += 1
    max_parallelism = max(counts.values()) if counts else 0

    return PlanReport(
        valid=True,
        pr_count=len(entries),
        levels=num_levels,
        max_parallelism=max_parallelism,
        linearized_order=order,
        level_assignments={pid: levels[pid] for pid in order},
        errors=[],
    )