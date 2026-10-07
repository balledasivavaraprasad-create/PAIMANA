"""Budget Reservation Subsystem.

Enforces pre-execution reservation of resources before tool dispatch,
preventing concurrent over-allocation and protecting emergency reserves.
"""
from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from .models import InvestigationBudget, ResourceConsumption


@dataclass
class BudgetReservation:
    """An active pre-execution hold on scarce investigation resources."""
    reservation_id: str
    tool_name: str
    estimated_cost: float
    estimated_latency_ms: float
    estimated_tokens: int
    external_calls: int
    is_emergency: bool = False
    status: str = "PENDING"  # PENDING, SETTLED, CANCELLED
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "reservation_id": self.reservation_id,
            "tool_name": self.tool_name,
            "estimated_cost": round(self.estimated_cost, 4),
            "estimated_latency_ms": self.estimated_latency_ms,
            "estimated_tokens": self.estimated_tokens,
            "external_calls": self.external_calls,
            "is_emergency": self.is_emergency,
            "status": self.status,
            "created_at": self.created_at,
        }


class ReservationManager:
    """Manages active reservations and settlement against the InvestigationBudget."""

    def __init__(self, budget: InvestigationBudget):
        self.budget = budget
        self.reservations: dict[str, BudgetReservation] = {}

    @property
    def reserved_cost(self) -> float:
        return sum(r.estimated_cost for r in self.reservations.values() if r.status == "PENDING")

    @property
    def reserved_calls(self) -> int:
        return sum(1 for r in self.reservations.values() if r.status == "PENDING")

    def reserve(
        self,
        tool_name: str,
        estimated_cost: float = 0.02,
        estimated_latency_ms: float = 200.0,
        estimated_tokens: int = 0,
        external_calls: int = 0,
        is_emergency: bool = False,
    ) -> Optional[BudgetReservation]:
        """Attempts to reserve requested resources. Returns None if budget cannot afford it."""
        # Account for already pending reservations in affordability check
        eff_budget = InvestigationBudget(
            max_iterations=self.budget.max_iterations,
            max_tool_calls=self.budget.max_tool_calls,
            max_llm_calls=self.budget.max_llm_calls,
            max_llm_tokens=self.budget.max_llm_tokens,
            max_external_calls=self.budget.max_external_calls,
            max_execution_seconds=self.budget.max_execution_seconds,
            max_estimated_cost=self.budget.max_estimated_cost,
            reserved_emergency_budget=self.budget.reserved_emergency_budget,
            consumed=ResourceConsumption(
                iterations=self.budget.consumed.iterations,
                tool_calls=self.budget.consumed.tool_calls + self.reserved_calls,
                llm_calls=self.budget.consumed.llm_calls,
                llm_input_tokens=self.budget.consumed.llm_input_tokens,
                llm_output_tokens=self.budget.consumed.llm_output_tokens,
                external_api_calls=self.budget.consumed.external_api_calls,
                execution_seconds=self.budget.consumed.execution_seconds,
                estimated_cost=self.budget.consumed.estimated_cost + self.reserved_cost,
            ),
            tool_calls_used=self.budget.tool_calls_used + self.reserved_calls,
        )

        if not eff_budget.can_afford(
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency_ms,
            estimated_tokens=estimated_tokens,
            external_calls=external_calls,
            is_emergency=is_emergency,
        ):
            return None

        res_id = f"res_{uuid.uuid4().hex[:8]}"
        res = BudgetReservation(
            reservation_id=res_id,
            tool_name=tool_name,
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency_ms,
            estimated_tokens=estimated_tokens,
            external_calls=external_calls,
            is_emergency=is_emergency,
            status="PENDING",
        )
        self.reservations[res_id] = res
        return res

    def settle(
        self,
        reservation_id: str,
        actual_latency_ms: float = 0.0,
        actual_cost: float = 0.0,
        actual_input_tokens: int = 0,
        actual_output_tokens: int = 0,
        actual_external_calls: int = 0,
    ) -> bool:
        """Settles an active reservation with actual execution measurements."""
        if reservation_id not in self.reservations:
            return False

        res = self.reservations[reservation_id]
        if res.status != "PENDING":
            return False

        res.status = "SETTLED"
        self.budget.record_call(
            latency_ms=actual_latency_ms,
            cost=actual_cost,
            input_tokens=actual_input_tokens,
            output_tokens=actual_output_tokens,
            external_calls=actual_external_calls,
        )
        return True

    def cancel(self, reservation_id: str) -> bool:
        """Cancels a pending reservation, releasing reserved capacity."""
        if reservation_id not in self.reservations:
            return False
        res = self.reservations[reservation_id]
        if res.status == "PENDING":
            res.status = "CANCELLED"
            return True
        return False
