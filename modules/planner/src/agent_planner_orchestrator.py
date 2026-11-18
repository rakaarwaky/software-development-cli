"""Planner agent orchestrator (AES agent layer).

Single agent that implements IPlanAggregate and orchestrates the three
planner capabilities (parse, validate, compute) through their protocols.
"""

from __future__ import annotations

from pathlib import Path

from shared.src.common.taxonomy_sdc_error import (
    PlanParseError,
    PlanUsageError,
    PlanValidationError,
)
from shared.src.planner.contract_planner_aggregate import IPlanAggregate
from shared.src.planner.contract_planner_protocol import (
    IPlanComputeProtocol,
    IPlanParseProtocol,
    IPlanValidateProtocol,
)
from shared.src.planner.taxonomy_planner_request import (
    PlanRequest,
    PlanResult,
    PrEntryList,
)

# ─── Block 1: Module Declaration ──────────────────────────────────────


class AgentPlanner(IPlanAggregate):
    """Agent orchestrator for the planner feature.

    Dispatches validate requests to the parse, validate, and compute
    capabilities in sequence.
    """

    def __init__(
        self,
        parser: IPlanParseProtocol,
        validator: IPlanValidateProtocol,
        computer: IPlanComputeProtocol,
    ) -> None:
        self._parser = parser
        self._validator = validator
        self._computer = computer

    # ─── Block 2: Module Contract ──────────────────────────────────────

    def execute(self, request: PlanRequest) -> PlanResult:
        """Run the plan validation the surface asked for; return the result."""
        if request.action == "validate":
            return self._validate(request.path)
        raise PlanUsageError(
            f"planner: unknown action {request.action!r}; expected 'validate'"
        )

    # ─── Block 3: Module Helpers ───────────────────────────────────────

    def _validate(self, path: str) -> PlanResult:
        """Run the full parse → validate → compute pipeline."""
        try:
            content = Path(path).read_text(encoding="utf-8")
        except FileNotFoundError:
            raise PlanUsageError(f"File not found: {path}")
        except OSError as exc:
            raise PlanUsageError(f"Cannot read file {path}: {exc}")

        # Step 1: Parse
        parse_result = self._parser.parse_plan(PrEntryList(text=content))
        if not parse_result.ok:
            raise PlanParseError("\n".join(parse_result.errors))

        # Step 2: Validate DAG
        validate_result = self._validator.validate_dag(
            PrEntryList(entries=parse_result.entries)
        )
        if not validate_result.ok:
            raise PlanValidationError("\n".join(validate_result.errors))

        # Step 3: Compute execution plan
        compute_result = self._computer.compute_levels(
            PrEntryList(entries=parse_result.entries)
        )

        return PlanResult(
            valid=True,
            pr_count=len(parse_result.entries),
            levels=compute_result.levels,
            max_parallelism=compute_result.max_parallelism,
            linearized_order=compute_result.linearized_order,
            level_assignments=compute_result.level_assignments,
            errors=list(parse_result.errors),
        )

    def __repr__(self) -> str:
        return "AgentPlanner()"