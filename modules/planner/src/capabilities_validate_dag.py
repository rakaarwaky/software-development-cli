"""DAG validator capability (AES capabilities layer, capability 2/3).

Implements IPlanValidateProtocol: validates unique IDs, valid
dependency references, and absence of cycles in the PR dependency DAG.
"""

from __future__ import annotations

from collections import defaultdict, deque

from shared.src.common.taxonomy_sdc_vo import PrEntry
from shared.src.planner.contract_planner_protocol import IPlanValidateProtocol
from shared.src.planner.taxonomy_planner_request import PrEntryList, ValidateResult

# ─── Block 1: Module Declaration ──────────────────────────────────────


class CapabilitiesValidateDag(IPlanValidateProtocol):
    """Capability: validate the PR dependency DAG."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def validate_dag(self, entries: PrEntryList) -> ValidateResult:
        """Validate dependency references and detect cycles."""
        pr_list = entries.entries
        errors: list[str] = []

        seen: set[str] = set()
        for entry in pr_list:
            if entry.id in seen:
                errors.append(f"Duplicate PR ID: '{entry.id}'")
            seen.add(entry.id)

        for entry in pr_list:
            for dep in entry.dependencies:
                if dep not in seen:
                    dep_label = dep.replace("pr-", "PR ", 1)
                    entry_label = entry.id.replace("pr-", "PR ", 1)
                    errors.append(
                        f"Dependency '{dep_label}' in {entry_label} "
                        f"does not reference a valid PR ID"
                    )

        if not errors:
            errors.extend(_detect_cycles(pr_list))

        return ValidateResult(ok=(len(errors) == 0), errors=errors)

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "CapabilitiesValidateDag()"


def _detect_cycles(entries: list[PrEntry]) -> list[str]:
    """Kahn's algorithm for topological sort; returns cycle errors."""
    in_degree: dict[str, int] = {e.id: 0 for e in entries}
    children: dict[str, list[str]] = defaultdict(list)
    dep_map: dict[str, list[str]] = {e.id: e.dependencies for e in entries}

    for entry in entries:
        for dep in entry.dependencies:
            children[dep].append(entry.id)
            in_degree[entry.id] += 1

    queue: deque[str] = deque(
        eid for eid, deg in in_degree.items() if deg == 0
    )
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


def _trace_cycle(
    dep_map: dict[str, list[str]], unvisited_ids: list[str]
) -> list[str] | None:
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