"""Temporal Reasoning and Precedence Validation Engine.

Enforces strict temporal consistency:
- Cause must precede effect.
- Intermediate variables must follow a monotonic chronological chain.
- If effect precedes cause, temporal consistency is violated and the hypothesis is weakened/rejected.
"""
from __future__ import annotations
import time
from typing import Optional
from .models import TemporalRelation


class TemporalReasoner:
    """Validates chronological ordering between candidate causes, mechanisms, and effects."""

    @classmethod
    def evaluate_temporal_order(
        cls,
        cause_event: str,
        effect_event: str,
        cause_timestamp: Optional[float],
        effect_timestamp: Optional[float],
        intermediate_events: Optional[list[tuple[str, float]]] = None
    ) -> TemporalRelation:
        """Evaluates whether cause precedes effect and checks sequence monotonicity."""
        intermediate_events = intermediate_events or []
        int_names = [name for name, _ in intermediate_events]

        # Case 1: Missing timestamps -> Plausible but unverified
        if cause_timestamp is None or effect_timestamp is None:
            return TemporalRelation(
                cause_event=cause_event,
                intermediate_events=int_names,
                effect_event=effect_event,
                cause_timestamp=cause_timestamp,
                effect_timestamp=effect_timestamp,
                lag_days=0.0,
                temporal_consistency=True,
                inconsistency_reason="Coarse or unverified timestamps; sequence inferred from reporting month without sub-monthly granularity."
            )

        lag_seconds = effect_timestamp - cause_timestamp
        lag_days = lag_seconds / 86400.0

        # Case 2: Temporal Inversion (Effect happened BEFORE Cause!)
        # Negative lag beyond a 1-day reporting tolerance means cause could not have driven effect.
        if lag_days < -1.0:
            return TemporalRelation(
                cause_event=cause_event,
                intermediate_events=int_names,
                effect_event=effect_event,
                cause_timestamp=cause_timestamp,
                effect_timestamp=effect_timestamp,
                lag_days=lag_days,
                temporal_consistency=False,
                inconsistency_reason=(
                    f"Temporal Inversion Detected: Effect '{effect_event}' occurred {abs(round(lag_days, 1))} days "
                    f"BEFORE candidate cause '{cause_event}'. An event cannot cause an earlier occurrence."
                )
            )

        # Case 3: Check Intermediate Chain Monotonicity
        current_time = cause_timestamp
        for name, ts in intermediate_events:
            if ts < current_time - 86400.0:
                return TemporalRelation(
                    cause_event=cause_event,
                    intermediate_events=int_names,
                    effect_event=effect_event,
                    cause_timestamp=cause_timestamp,
                    effect_timestamp=effect_timestamp,
                    lag_days=lag_days,
                    temporal_consistency=False,
                    inconsistency_reason=(
                        f"Non-monotonic intermediate chain: intermediate variable '{name}' occurred "
                        f"prior to root cause '{cause_event}'."
                    )
                )
            current_time = ts

        # Case 4: Chronologically Valid Sequence
        return TemporalRelation(
            cause_event=cause_event,
            intermediate_events=int_names,
            effect_event=effect_event,
            cause_timestamp=cause_timestamp,
            effect_timestamp=effect_timestamp,
            lag_days=lag_days,
            temporal_consistency=True,
            inconsistency_reason=None
        )

    @classmethod
    def calculate_temporal_support(cls, rel: TemporalRelation) -> float:
        """Computes normalized temporal support score in [0.05, 1.0]."""
        if not rel.temporal_consistency:
            return 0.05  # Severe penalty for temporal impossibility

        if rel.cause_timestamp is None or rel.effect_timestamp is None:
            return 0.50  # Coarse / provisional baseline

        # Plausible infrastructure lag curve:
        # 10 to 180 days lag is optimal for capital works transmission
        if 0.0 <= rel.lag_days <= 180.0:
            return 0.95
        elif rel.lag_days <= 365.0:
            return 0.85
        elif rel.lag_days <= 730.0:
            return 0.70
        else:
            # Over 2 years lag: temporal connection becomes distant
            return 0.40
