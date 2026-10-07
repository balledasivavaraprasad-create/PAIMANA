"""Hypothesis Discriminator and Dynamic Information Gain Evaluator.

Evaluates how effectively candidate tools discriminate competing hypotheses
and resolve active EvidenceNeeds without relying on static event mappings.
"""
from __future__ import annotations
import math
from typing import Any
from .evidence_need import EvidenceNeed


class HypothesisDiscriminator:
    """Computes dynamic information gain and hypothesis discrimination power for tools."""

    def evaluate_tool_information_gain(self, tool_def: Any, open_needs: list[EvidenceNeed],
                                      hypotheses: list[Any], state: Any) -> tuple[float, float, list[str]]:
        """Calculates (expected_information_gain, discrimination_power, addressed_need_ids)."""
        tool_name = tool_def.name
        capabilities = set(getattr(tool_def, "capabilities", []))
        ev_types = set(getattr(tool_def, "evidence_types_generated", []))
        hypo_domains = set(getattr(tool_def, "hypothesis_domains", []))
        disc_targets = getattr(tool_def, "discrimination_targets", [])

        addressed_needs: list[str] = []
        gain_contributions: list[float] = []
        max_disc = 0.10

        # Identify which active open needs this tool can satisfy
        for need in open_needs:
            if need.status != "OPEN":
                continue

            matches_ev = bool(set(need.required_evidence_types).intersection(ev_types))
            matches_direct = (tool_name in need.id)

            # Tool must be capable of generating the required evidence type or directly targeted
            if not (matches_ev or matches_direct):
                continue

            matches_hypo = bool(set(need.target_hypothesis_ids).intersection(hypo_domains)) if need.target_hypothesis_ids else True

            if matches_hypo or matches_direct:
                addressed_needs.append(need.id)
                # Gain is proportional to need priority and urgency
                gain_contribution = (need.priority * 0.65 + need.urgency * 0.35)
                gain_contributions.append(gain_contribution)
                max_disc = max(max_disc, need.discrimination_power)

        if not addressed_needs:
            return 0.02, 0.05, []

        # --------------------------------------------------------------------
        # Dynamic Hypothesis Uncertainty & Discrimination Boost
        # --------------------------------------------------------------------
        # Inspect top competing hypotheses to see how closely contested they are
        active_hypos = [h for h in hypotheses if getattr(h, "status", "").lower() in ["active", "supported", "primary", "candidate"]]
        hypothesis_uncertainty = 1.0
        competing_pair_targeted = False

        if len(active_hypos) >= 2:
            def _get_conf(h):
                c = getattr(h, "confidence_score", getattr(h, "confidence", 0.5))
                if isinstance(c, str):
                    return 0.85 if c == "HIGH" else (0.50 if c == "MEDIUM" else 0.20)
                return float(c)

            c1 = _get_conf(active_hypos[0])
            c2 = _get_conf(active_hypos[1])
            diff = abs(c1 - c2)
            
            # Highest uncertainty when margin is small (e.g. 50/50 split -> diff ~ 0.0)
            hypothesis_uncertainty = max(0.20, 1.0 - diff)

            id1 = getattr(active_hypos[0], "id", "")
            id2 = getattr(active_hypos[1], "id", "")
            domain1 = getattr(active_hypos[0], "domain", id1)
            domain2 = getattr(active_hypos[1], "domain", id2)

            # Check if this tool has explicit discrimination capability for the competing pair
            for (t1, t2) in disc_targets:
                if (t1 in [id1, domain1] and t2 in [id2, domain2]) or (t2 in [id1, domain1] and t1 in [id2, domain2]):
                    competing_pair_targeted = True
                    break

            # Or if tool targets at least one of the top competing hypotheses
            if id1 in hypo_domains or domain1 in hypo_domains:
                max_disc = max(max_disc, 0.75)
            if id2 in hypo_domains or domain2 in hypo_domains:
                max_disc = max(max_disc, 0.75)

        # Compute total information gain with diminishing returns for multiple needs
        gain_contributions.sort(reverse=True)
        total_need_gain = 0.0
        decay = 1.0
        for gc in gain_contributions:
            total_need_gain += gc * decay
            decay *= 0.35

        if competing_pair_targeted:
            max_disc = min(1.0, max_disc + 0.25)
            total_need_gain *= 1.20

        norm_gain = min(1.0, max(0.05, total_need_gain * hypothesis_uncertainty))

        return round(norm_gain, 3), round(max_disc, 3), addressed_needs
