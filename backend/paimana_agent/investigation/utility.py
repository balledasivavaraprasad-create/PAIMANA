"""Multi-Criteria Tool Utility Evaluator.

Scores candidate tools dynamically on expected information gain, discrimination power,
source authority, and freshness, reduced by execution cost, latency, redundancy, and failure penalties.
"""
from __future__ import annotations
import math
from typing import Any, Optional
from .candidate import ToolCandidate
from .evidence_need import EvidenceNeed
from .discriminator import HypothesisDiscriminator


class ToolUtilityEvaluator:
    """Evaluates multi-criteria utility for candidate investigation tools."""

    def __init__(self,
                 w_gain: float = 0.35,
                 w_disc: float = 0.25,
                 w_auth: float = 0.15,
                 w_fresh: float = 0.10,
                 w_cost: float = 0.08,
                 w_lat: float = 0.07):
        self.w_gain = w_gain
        self.w_disc = w_disc
        self.w_auth = w_auth
        self.w_fresh = w_fresh
        self.w_cost = w_cost
        self.w_lat = w_lat
        self.discriminator = HypothesisDiscriminator()

    def evaluate_candidate(self, tool_def: Any, state: Any,
                           open_needs: list[EvidenceNeed],
                           caller_authorization: str = "read_only",
                           store_available: bool = True,
                           model_available: bool = True,
                           custom_freshness: Optional[float] = None) -> ToolCandidate:
        """Evaluates a single tool and produces a structured ToolCandidate."""
        tool_name = tool_def.name
        prereqs = getattr(tool_def, "prerequisites", [])
        ineligibility: list[str] = []

        # --------------------------------------------------------------------
        # 1. Prerequisite & Permission Gating
        # --------------------------------------------------------------------
        if "store" in prereqs and not store_available:
            ineligibility.append("Prerequisite database store is unavailable")

        if "model" in prereqs and not model_available:
            ineligibility.append("Prerequisite predictive model or background reference is unavailable")

        tool_auth = getattr(tool_def, "authorization_required", "read_only")
        if tool_auth == "privileged" and caller_authorization != "privileged":
            ineligibility.append(f"Tool requires elevated authorization '{tool_auth}' (caller has '{caller_authorization}')")

        # Circuit breaker gating
        cb = getattr(tool_def, "circuit_breaker", None)
        if cb and hasattr(cb, "can_execute") and not cb.can_execute():
            ineligibility.append(f"Circuit breaker is OPEN for tool '{tool_name}'")

        eligible = (len(ineligibility) == 0)

        # --------------------------------------------------------------------
        # 2. Dynamic Information Gain & Discrimination Power
        # --------------------------------------------------------------------
        hypotheses = getattr(state, "hypotheses", [])
        gain, disc, addressed = self.discriminator.evaluate_tool_information_gain(
            tool_def, open_needs, hypotheses, state
        )

        # --------------------------------------------------------------------
        # 3. Source Authority & Freshness
        # --------------------------------------------------------------------
        auth = float(getattr(tool_def, "source_authority", 0.80))
        fresh = custom_freshness if custom_freshness is not None else 1.0

        # --------------------------------------------------------------------
        # 4. Operational Costs & Penalties
        # --------------------------------------------------------------------
        cost = float(getattr(tool_def, "execution_cost", 0.10))
        lat_ms = float(getattr(tool_def, "typical_latency_ms", 25.0))
        lat_norm = min(1.0, lat_ms / 200.0)

        # Redundancy penalty: heavily penalize repeated tool runs on same static data
        used_tools = getattr(state, "tools_used", [])
        redundancy_penalty = 0.0
        if tool_name in used_tools:
            redundancy_penalty += 0.60
        
        # Lineage / Group redundancy check
        source_sys = getattr(tool_def, "source_system", "PAIMANA")
        ev_groups = getattr(state, "evidence_groups", {})
        if source_sys in ev_groups and ev_groups[source_sys].effective_group_weight >= 0.90:
            redundancy_penalty += 0.15

        # Failure penalty: penalize tools that recently threw errors
        failure_penalty = 0.0
        executions = getattr(state, "tool_executions", [])
        for ex in executions:
            if ex.tool_name == tool_name and ex.status != "SUCCESS":
                failure_penalty = 0.85
                break

        # --------------------------------------------------------------------
        # 5. Net Utility Formula & Reliability Grounding
        # --------------------------------------------------------------------
        exec_rel = float(getattr(tool_def, "historical_reliability", 0.98))
        ev_rel = float(getattr(tool_def, "source_authority", 0.85))
        prof = getattr(tool_def, "reliability_profile", None)
        if prof:
            if hasattr(prof, "execution_reliability"):
                exec_rel = prof.execution_reliability
            if hasattr(prof, "evidence_reliability"):
                ev_rel = prof.evidence_reliability
        comp_rel = round(0.50 * exec_rel + 0.50 * ev_rel, 3)

        effective_auth = auth * ev_rel
        info_val = round((self.w_gain * gain + self.w_disc * disc) / max(0.01, self.w_gain + self.w_disc), 3)

        raw_utility = (
            self.w_gain * gain +
            self.w_disc * disc +
            self.w_auth * effective_auth +
            self.w_fresh * fresh -
            self.w_cost * cost -
            self.w_lat * lat_norm -
            redundancy_penalty -
            failure_penalty
        )

        weighted_utility = raw_utility * exec_rel
        net_utility = max(0.0, min(1.0, weighted_utility)) if eligible else 0.0

        # Selection rationale
        rationale_parts = []
        if not eligible:
            rationale_parts.append(f"Ineligible: {'; '.join(ineligibility)}")
        else:
            rationale_parts.append(f"InfoVal: {info_val:.2f} (Gain={gain:.2f}, Disc={disc:.2f}), Auth: {auth:.2f}, ExecRel: {exec_rel:.2f}, EvRel: {ev_rel:.2f}")
            if addressed:
                rationale_parts.append(f"Addresses needs: {addressed}")
            if redundancy_penalty > 0:
                rationale_parts.append(f"Redundancy penalty: -{redundancy_penalty:.2f}")
            if failure_penalty > 0:
                rationale_parts.append(f"Prior failure penalty: -{failure_penalty:.2f}")

        rationale = f"{tool_name} (net_utility={net_utility:.3f}): " + " | ".join(rationale_parts)

        return ToolCandidate(
            tool_name=tool_name,
            target_needs=addressed,
            information_value=info_val,
            expected_information_gain=gain,
            discrimination_power=disc,
            source_authority=auth,
            execution_reliability=exec_rel,
            evidence_reliability=ev_rel,
            composite_reliability=comp_rel,
            expected_freshness=fresh,
            execution_cost=cost,
            expected_latency_ms=lat_ms,
            redundancy_penalty=redundancy_penalty,
            failure_penalty=failure_penalty,
            net_utility=net_utility,
            selection_rationale=rationale,
            eligible=eligible,
            ineligibility_reasons=ineligibility,
        )
