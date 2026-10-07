"""Resource Accounting Ledger.

Maintains an immutable, auditable log of estimated vs actual resource consumption,
cost variance, and execution latency across all investigation steps.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ResourceLedgerEntry:
    """Individual accounting entry comparing estimated vs actual resource consumption."""
    investigation_id: str
    operation_id: str
    resource_type: str
    resource_name: str
    estimated_quantity: float
    actual_quantity: float
    variance: float = 0.0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    timestamp: float = field(default_factory=time.time)
    status: str = "SETTLED"

    def __post_init__(self):
        self.variance = round(self.actual_quantity - self.estimated_quantity, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "operation_id": self.operation_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "estimated_quantity": self.estimated_quantity,
            "actual_quantity": self.actual_quantity,
            "variance": self.variance,
            "estimated_cost": round(self.estimated_cost, 4),
            "actual_cost": round(self.actual_cost, 4),
            "timestamp": self.timestamp,
            "status": self.status,
        }


class ResourceLedger:
    """Ledger tracking historical resource consumption and variance."""

    def __init__(self, investigation_id: str = ""):
        self.investigation_id = investigation_id
        self.entries: list[ResourceLedgerEntry] = []

    def record_entry(
        self,
        operation_id: str,
        resource_type: str,
        resource_name: str,
        estimated_quantity: float,
        actual_quantity: float,
        estimated_cost: float = 0.0,
        actual_cost: float = 0.0,
        status: str = "SETTLED",
    ) -> ResourceLedgerEntry:
        """Records a completed operation in the ledger."""
        entry = ResourceLedgerEntry(
            investigation_id=self.investigation_id,
            operation_id=operation_id,
            resource_type=resource_type,
            resource_name=resource_name,
            estimated_quantity=estimated_quantity,
            actual_quantity=actual_quantity,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost,
            status=status,
        )
        self.entries.append(entry)
        return entry

    @property
    def total_estimated_cost(self) -> float:
        return sum(e.estimated_cost for e in self.entries)

    @property
    def total_actual_cost(self) -> float:
        return sum(e.actual_cost for e in self.entries)

    @property
    def cost_variance(self) -> float:
        return round(self.total_actual_cost - self.total_estimated_cost, 4)

    def get_variance_summary(self) -> dict[str, Any]:
        """Summarizes estimation accuracy across all ledger operations."""
        if not self.entries:
            return {
                "total_entries": 0,
                "total_estimated_cost": 0.0,
                "total_actual_cost": 0.0,
                "cost_variance": 0.0,
                "mean_quantity_variance": 0.0,
            }

        mean_var = sum(abs(e.variance) for e in self.entries) / len(self.entries)
        return {
            "total_entries": len(self.entries),
            "total_estimated_cost": round(self.total_estimated_cost, 4),
            "total_actual_cost": round(self.total_actual_cost, 4),
            "cost_variance": self.cost_variance,
            "mean_quantity_variance": round(mean_var, 3),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "investigation_id": self.investigation_id,
            "entries_count": len(self.entries),
            "variance_summary": self.get_variance_summary(),
            "entries": [e.to_dict() for e in self.entries],
        }
