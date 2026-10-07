"""Pattern Fingerprint Builder and Structured Pattern Matcher.

Extracts compact anomaly fingerprints from project metrics and evaluates
structured, non-semantic similarity between historical precedents and live cases.
"""
from __future__ import annotations
from typing import Any, Optional
from .models import PatternFingerprint


class PatternFingerprintBuilder:
    """Builds structured PatternFingerprint representations from raw project state."""

    @staticmethod
    def build_fingerprint(p: dict, feats: Optional[dict] = None,
                          events: Optional[list[dict]] = None,
                          observations: Optional[dict] = None) -> PatternFingerprint:
        feats = feats or {}
        events = events or []
        observations = observations or {}

        # 1. Event Type
        event_types = [e.get("type", "") for e in events if isinstance(e, dict)]
        if "COST_PROGRESS_MISMATCH" in event_types:
            ev_type = "cost_progress_mismatch"
        elif "MILESTONE_DELAYED" in event_types:
            ev_type = "milestone_delayed"
        elif "PROGRESS_STALLED" in event_types:
            ev_type = "progress_stalled"
        elif "RISK_ACCELERATING" in event_types:
            ev_type = "risk_accelerating"
        elif event_types:
            ev_type = event_types[0].lower()
        else:
            ev_type = "general_review"

        # 2. Financial Velocity
        spend = float(p.get("cumulative_expenditure_cr") or 0.0)
        cost = float(p.get("original_cost_cr") or 1.0)
        prog = float(p.get("physical_progress_pct") or 0.0)
        spend_pct = (spend / cost * 100.0) if cost > 0 else 0.0
        gap = float(feats.get("progress_expenditure_gap_pct", spend_pct - prog))

        if gap > 15.0:
            fin_vel = "decoupled"
        elif gap > 5.0:
            fin_vel = "ahead"
        elif gap < -5.0:
            fin_vel = "behind"
        else:
            fin_vel = "balanced"

        # 3. Milestone Slippage
        slip = float(feats.get("completion_delay_months", 0.0))
        if slip >= 12.0:
            mile_slip = "persistent"
        elif slip > 0.0:
            mile_slip = "moderate"
        else:
            mile_slip = "none"

        # 4. Risk Direction & Velocity
        jump = float(feats.get("recent_score_jump", 0.0))
        if jump >= 8.0 or "RISK_ACCELERATING" in event_types:
            risk_dir = "increasing"
            risk_vel = "fast"
        elif jump > 0.0:
            risk_dir = "increasing"
            risk_vel = "moderate"
        elif jump < 0.0:
            risk_dir = "decreasing"
            risk_vel = "slow"
        else:
            risk_dir = "stable"
            risk_vel = "slow"

        # 5. Progress Variance
        age_ratio = float(feats.get("age_to_planned_ratio", 0.0))
        if age_ratio > 0.7 and prog < 25.0:
            prog_var = "high"
        elif age_ratio > 0.5 and prog < 40.0:
            prog_var = "moderate"
        else:
            prog_var = "low"

        # 6. Specific Constraints (Approval / Contractor)
        issues = p.get("detected_issues", [])
        if isinstance(issues, list):
            issues_str = " ".join(str(i).lower() for i in issues)
        else:
            issues_str = ""

        approval_delay = "high" if any(w in issues_str for w in ["approval", "clearance", "land", "forest"]) else "low"
        contractor_delay = "high" if any(w in issues_str for w in ["contractor", "mobilization", "manpower", "equipment"]) else "low"

        return PatternFingerprint(
            event_type=ev_type,
            risk_direction=risk_dir,
            risk_velocity=risk_vel,
            progress_variance=prog_var,
            milestone_slippage=mile_slip,
            financial_velocity=fin_vel,
            approval_delay=approval_delay,
            contractor_delay=contractor_delay,
        )


class PatternMatcher:
    """Computes structured pattern similarity between two PatternFingerprints."""

    WEIGHTS = {
        "event_type": 0.20,
        "financial_velocity": 0.25,
        "milestone_slippage": 0.20,
        "progress_variance": 0.15,
        "risk_velocity": 0.10,
        "risk_direction": 0.05,
        "approval_delay": 0.025,
        "contractor_delay": 0.025,
    }

    @classmethod
    def similarity(cls, f1: PatternFingerprint, f2: PatternFingerprint) -> float:
        """Returns normalized structured similarity in [0.0, 1.0]."""
        score = 0.0
        for field_name, weight in cls.WEIGHTS.items():
            val1 = getattr(f1, field_name, None)
            val2 = getattr(f2, field_name, None)
            if val1 == val2 and val1 is not None:
                score += weight
            elif field_name == "financial_velocity" and {val1, val2}.issubset({"decoupled", "ahead"}):
                score += weight * 0.70  # Partial credit for related spend anomalies
            elif field_name == "milestone_slippage" and {val1, val2}.issubset({"persistent", "moderate"}):
                score += weight * 0.75  # Partial credit for related slippage levels
        return round(min(1.0, max(0.0, score)), 3)
