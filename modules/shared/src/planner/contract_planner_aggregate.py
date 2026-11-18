"""Planner-domain contract (AES contract layer, ABC trait).

Single entry point over the PR Plan validator capability: validate_plan.
The CLI surface calls ``execute`` with a ``PlanRequest`` and gets a
``PlanResult`` back.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.planner.taxonomy_planner_request import PlanRequest, PlanResult


class IPlanAggregate(ABC):
    """Single entry point over the PR Plan validator capability."""

    @abstractmethod
    def execute(self, request: PlanRequest) -> PlanResult:
        """Run the plan validation the surface asked for; return the result."""
        ...