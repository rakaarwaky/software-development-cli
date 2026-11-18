"""Execution plan computer capability (AES capabilities layer, capability 3/3).

Implements IPlanComputeProtocol: computes level assignments,
max parallelism, and linearizes for final branch merge order.
"""

from __future__ import annotations

import re
from collections import defaultdict, deque

from shared.src.common.taxonomy_sdc_vo import PrEntry
from shared.src.planner.contract_planner_protocol import IPlanComputeProtocol
from shared.src.planner.taxonomy_planner_request import ComputeResult, PrEntryList

# ─── Block 1: Module Declaration ──────────────────────────────────────


class CapabilitiesComputeExecution(IPlanComputeProtocol):
    """Capability: compute level assignments and linearization."""

    def __init__(self) -> None:
        pass

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def compute_levels(self, entries: PrEntryList) -> ComputeResult:
        """Compute level assignments, max parallelism, and linearization."""
        pr_list = entries.entries
        levels_map = _compute_levels_map(pr_list)
        order = _linearize(pr_list, levels_map)

        num_levels = max(levels_map.values()) + 1 if levels_map else 0
        counts: dict[int, int] = defaultdict(int)
        for lv in levels_map.values():
            counts[lv] += 1
        max_parallelism = max(counts.values()) if counts else 0

        return ComputeResult(
            ok=True,
            levels=num_levels,
            max_parallelism=max_parallelism,
            linearized_order=order,
            level_assignments={pid: levels_map[pid] for pid in order},
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def __repr__(self) -> str:
        return "CapabilitiesComputeExecution()"


def _pr_sort_key(pr_id: str) -> tuple[int, int, int, str]:
    """Sort numeric PR ids numerically, then lettered ids after them."""
    suffix = pr_id.split("-", 1)[1] if "-" in pr_id else pr_id
    match = re.fullmatch(r"(\d+)([a-z]*)", suffix)
    if match:
        number = int(match.group(1))
        letters = match.group(2)
        return (0 if not letters else 1, number, len(letters), letters)
    return (2, 0, 0, suffix)


def _compute_levels_map(entries: list[PrEntry]) -> dict[str, int]:
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


def _linearize(
    entries: list[PrEntry], levels: dict[str, int]
) -> list[str]:
    """Flatten the DAG into final branch merge order (stable within levels)."""
    by_level: dict[int, list[str]] = defaultdict(list)
    for e in entries:
        by_level[levels[e.id]].append(e.id)

    order: list[str] = []
    for lv in sorted(by_level):
        order.extend(sorted(by_level[lv], key=_pr_sort_key))
    return order