"""Temporal Decay Engine for Institutional Knowledge.

Applies domain-specific half-life decay to precedent relevance so that older,
potentially obsolete administrative precedents do not indefinitely dominate
active recommendations.
"""
from __future__ import annotations
import math
import time
from typing import Optional


class MemoryDecayManager:
    """Calculates temporal decay weighting for precedents based on domain half-life."""

    # Default half-lives in days
    HALF_LIVES_DAYS = {
        "statutory_policy": 180.0,       # Regulations, circulars change rapidly (~6 months)
        "contractual_norms": 365.0,      # Contract standard templates (~1 year)
        "cost_benchmarks": 365.0,       # Inflation, material pricing (~1 year)
        "engineering_patterns": 1095.0,  # Physical geology, civil engineering (~3 years)
        "general_infrastructure": 730.0, # Standard default (~2 years)
    }

    SECONDS_PER_DAY = 86400.0

    @classmethod
    def calculate_decay(cls, created_at: float,
                        now: Optional[float] = None,
                        domain: str = "general_infrastructure") -> float:
        """Returns temporal weight in (0.0, 1.0].

        decay = 2 ** (-age_days / half_life_days)
        """
        now = now or time.time()
        age_seconds = max(0.0, now - created_at)
        age_days = age_seconds / cls.SECONDS_PER_DAY

        half_life = cls.HALF_LIVES_DAYS.get(domain, cls.HALF_LIVES_DAYS["general_infrastructure"])
        decay = math.pow(0.5, age_days / half_life)
        return round(min(1.0, max(0.05, decay)), 3)
