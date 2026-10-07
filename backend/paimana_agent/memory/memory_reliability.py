"""Precedent Reliability and Anti-Circular Corroboration Engine.

Calculates the empirical reliability of a precedent while preventing circular
inflation (e.g. repeated runs of the same project model falsely counting as
independent confirmations).
"""
from __future__ import annotations
from typing import Optional
from .models import Precedent, PrecedentProvenance


class MemoryReliabilityManager:
    """Computes empirical reliability score for precedents."""

    @classmethod
    def compute_reliability(cls, precedent: Precedent) -> float:
        """Calculates reliability in [0.1, 1.0] using Bayesian track record,

        independent corroboration, and root cause evidence strength.
        """
        # 1. Empirical Track Record with Laplace Smoothing
        successes = max(0, precedent.success_count)
        failures = max(0, precedent.failure_count)
        total = successes + failures
        if total == 0:
            track_record = 0.50
        else:
            # Beta prior equivalent: (successes + 1) / (total + 2)
            track_record = (successes + 1.0) / (total + 2.0)

        # 2. Independent Corroboration (Discounting for circular reuse)
        unique_groups = set(precedent.provenance.independence_group_ids)
        # Also count source project as an implicit group if not already represented
        if precedent.source_project_id:
            unique_groups.add(f"proj_{precedent.source_project_id}")

        n_groups = len(unique_groups)
        if n_groups <= 1:
            independence_factor = 0.70  # Single source, not yet cross-verified
        elif n_groups == 2:
            independence_factor = 0.85
        elif n_groups >= 3:
            independence_factor = 1.00  # Multiple independent sources

        # 3. Base Evidentiary Strength of Root Cause
        base_confidence = min(1.0, max(0.20, precedent.root_cause_confidence))

        # 4. Status Multiplier
        status_mult = {
            "VALIDATED": 1.0,
            "PROVISIONAL": 0.75,
            "CANDIDATE": 0.50,
            "STALE": 0.40,
            "CONTRADICTED": 0.10,
            "REJECTED": 0.05,
            "SUPERSEDED": 0.30,
        }.get(precedent.status, 0.50)

        # Combined weighted reliability
        raw = (0.45 * track_record + 0.30 * base_confidence + 0.25 * independence_factor) * status_mult
        return round(min(1.0, max(0.05, raw)), 3)

    @classmethod
    def record_application_outcome(cls, precedent: Precedent, success: bool,
                                   independence_group: Optional[str] = None) -> Precedent:
        """Updates empirical application counts and independence groups, recalculating reliability."""
        precedent.application_count += 1
        if success:
            precedent.success_count += 1
        else:
            precedent.failure_count += 1

        if independence_group and independence_group not in precedent.provenance.independence_group_ids:
            precedent.provenance.independence_group_ids.append(independence_group)

        precedent.memory_reliability = cls.compute_reliability(precedent)
        return precedent
