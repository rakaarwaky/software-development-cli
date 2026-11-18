"""Planner-domain capability contracts (AES contract layer, ABC).

Three rich protocol ABCs for the PR Plan validator feature:
  IPlanParseProtocol      — Parse the ## PR Plan section
  IPlanValidateProtocol    — Validate the PR dependency DAG
  IPlanComputeProtocol     — Compute level assignments and linearization
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from shared.src.planner.taxonomy_planner_request import (
    ComputeResult,
    ParseResult,
    PrEntryList,
    ValidateResult,
)


class IPlanParseProtocol(ABC):
    """Parse the ``## PR Plan`` section of a design document."""

    @abstractmethod
    def parse_plan(self, plan_text: str) -> ParseResult:
        """Parse ``plan_text`` into PR entries or a parse error."""
        ...


class IPlanValidateProtocol(ABC):
    """Validate the PR dependency DAG."""

    @abstractmethod
    def validate_dag(self, entries: PrEntryList) -> ValidateResult:
        """Validate dependency references and detect cycles."""
        ...


class IPlanComputeProtocol(ABC):
    """Compute level assignments and final merge order."""

    @abstractmethod
    def compute_levels(self, entries: PrEntryList) -> ComputeResult:
        """Compute level assignments, max parallelism, and linearization."""
        ...


__all__ = [
    "IPlanComputeProtocol",
    "IPlanParseProtocol",
    "IPlanValidateProtocol",
]

_layer_symbols = {
    "IPlanParseProtocol": IPlanParseProtocol,
    "IPlanValidateProtocol": IPlanValidateProtocol,
    "IPlanComputeProtocol": IPlanComputeProtocol,
}