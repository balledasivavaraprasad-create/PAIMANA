"""Reopen Policy Manager.

Manages hysteresis to prevent noisy reopening of converged investigations while
ensuring that genuine material events (risk spikes, new authoritative evidence,
contradictions, or intervention failures) trigger an investigation reopening.
"""
from __future__ import annotations
from typing import Any
from .models import ReopenTrigger


class ReopenPolicyManager:
    """Evaluates whether new project observations warrant reopening an investigation."""

    MATERIAL_RISK_DELTA_THRESHOLD = 15.0  # +15 pt risk shift warrants reopening
    AUTHORITY_OVERRIDE_THRESHOLD = 0.85   # Authoritative ground truth overrides previous closure

    @classmethod
    def should_reopen(
        cls,
        previous_termination: Any,
        trigger: ReopenTrigger
    ) -> tuple[bool, str]:
        """Evaluates whether to reopen: (can_reopen, rationale).

        Uses hysteresis: minor evidence additions do NOT reopen converged investigations.
        """
        trig_type = trigger.trigger_type.upper()
        mat = trigger.materiality
        sev = trigger.severity.upper()

        # 1. Authoritative ground-truth evidence strictly overrides prior closure
        if trig_type == "NEW_AUTHORITATIVE_EVIDENCE":
            if mat >= cls.AUTHORITY_OVERRIDE_THRESHOLD or sev in ["HIGH", "CRITICAL"]:
                return True, f"Reopened: High-authority new evidence arrived ({trigger.description or trig_type})."
            return False, f"Suppressed: Evidence materiality ({mat:.2f}) below authoritative override threshold ({cls.AUTHORITY_OVERRIDE_THRESHOLD})."

        # 2. Material project risk escalation
        if trig_type == "MATERIAL_RISK_CHANGE":
            if mat >= cls.MATERIAL_RISK_DELTA_THRESHOLD or sev in ["HIGH", "CRITICAL"]:
                return True, f"Reopened: Project risk shifted materially by {mat:.1f} pts ({trigger.description})."
            return False, f"Suppressed: Risk shift ({mat:.1f} pts) below materiality threshold ({cls.MATERIAL_RISK_DELTA_THRESHOLD} pts)."

        # 3. Direct Causal Contradiction
        if trig_type == "CAUSAL_CONTRADICTION":
            return True, f"Reopened: Prior causal conclusion directly contradicted by new field telemetry ({trigger.description})."

        # 4. Intervention Failure (Closed-loop learning)
        if trig_type == "INTERVENTION_FAILURE":
            return True, f"Reopened: Recommended intervention failed to resolve milestone slippage ({trigger.description})."

        # 5. Data Correction in authoritative record
        if trig_type == "DATA_CORRECTION":
            if sev in ["HIGH", "CRITICAL"] or mat >= 0.50:
                return True, f"Reopened: Official historical project ledger corrected ({trigger.description})."
            return False, "Suppressed: Minor reporting adjustment does not justify full re-investigation."

        return False, "Suppressed by hysteresis: trigger does not satisfy materiality criteria."
