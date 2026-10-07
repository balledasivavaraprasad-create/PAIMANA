"""Hypothesis Scorer & State Transition Engine.

Implements an evidence-weighted support model aggregated across independent source groups.
Explicitly distinguishes independent corroboration from single-snapshot analytical agreement.
Calculates Evidence Support Score and manages hypothesis status transitions.
"""
from __future__ import annotations
import time
from typing import Any, Optional
from .model import Hypothesis
from ..evidence.model import Evidence, ConfidenceUpdate


class HypothesisScorer:
    """Evaluates supporting and contradicting evidence aggregated across independent groups."""

    def score_and_transition(
        self,
        hypotheses: list[Hypothesis],
        evidence_items: list[Any],
        iteration: int,
        confidence_history: Optional[list[ConfidenceUpdate]] = None
    ) -> None:
        """Updates supporting_score, contradicting_score, confidence, and status for each hypothesis."""
        evidence_by_id = {e.id: e for e in evidence_items}

        # 1. Group evidence by independence_group_id
        groups: dict[str, list[Evidence]] = {}
        for ev in evidence_items:
            gid = getattr(ev, "independence_group_id", getattr(ev, "independence_group", "default"))
            if gid not in groups:
                groups[gid] = []
            groups[gid].append(ev)

        for h in hypotheses:
            prev_score = h.confidence if isinstance(h.confidence, (int, float)) else 0.50
            h.last_updated_iteration = iteration

            # Sync evidence linkages from evidence_items
            tgt = h.id
            for ev in evidence_items:
                supports = getattr(ev, "supports_hypotheses", [])
                contradicts = getattr(ev, "contradicts_hypotheses", [])
                if any(tgt == s or f"hypothesis:{tgt}" == s for s in supports):
                    if ev.id not in h.support_evidence_ids:
                        h.support_evidence_ids.append(ev.id)
                if any(tgt == c or f"hypothesis:{tgt}" == c for c in contradicts):
                    if ev.id not in h.contradiction_evidence_ids:
                        h.contradiction_evidence_ids.append(ev.id)

            # 2. Independent Group-Level Aggregation for Support
            supporting_groups: list[str] = []
            total_support = 0.0

            for gid, g_items in groups.items():
                g_supporting = [e for e in g_items if e.id in h.support_evidence_ids]
                if not g_supporting:
                    continue

                supporting_groups.append(gid)

                # Separate primary direct observations from derived/model metrics
                primaries = [e for e in g_supporting if getattr(e, "evidence_type", "direct_observation") != "derived_metric"]
                derived = [e for e in g_supporting if getattr(e, "evidence_type", "direct_observation") == "derived_metric"]

                # Base primary strength in this group
                if primaries:
                    base_strength = max(e.calculate_effective_strength() if hasattr(e, "calculate_effective_strength") else getattr(e, "reliability", 1.0) for e in primaries)
                else:
                    base_strength = max(e.calculate_effective_strength() if hasattr(e, "calculate_effective_strength") else getattr(e, "reliability", 1.0) for e in derived) * 0.70

                # Capped contribution from derived evidence within the same group
                derived_sum = sum(e.calculate_effective_strength() if hasattr(e, "calculate_effective_strength") else getattr(e, "reliability", 1.0) for e in derived)
                derived_contrib = min(0.35, 0.25 * derived_sum)

                # Group contribution capped at 1.0 (prevents multiple tools on same snapshot from inflating score)
                group_strength = min(1.0, base_strength + derived_contrib)
                total_support += group_strength

            # Independent Corroboration Reward: Reward true multi-group independent corroboration
            num_indep = len(supporting_groups)
            if num_indep >= 2:
                corrob_boost = 0.20 * (num_indep - 1)
                total_support += corrob_boost

            # 3. Independent Group-Level Aggregation for Contradiction
            contradicting_groups: list[str] = []
            total_contra = 0.0

            for gid, g_items in groups.items():
                g_contradicting = [e for e in g_items if e.id in h.contradiction_evidence_ids]
                if not g_contradicting:
                    continue

                contradicting_groups.append(gid)
                # Strongest contradiction in this group
                group_contra = max(e.calculate_effective_strength() if hasattr(e, "calculate_effective_strength") else (getattr(e, "reliability", 1.0) * 1.5) for e in g_contradicting)
                total_contra += group_contra

            # 4. Compute Scores
            h.supporting_score = round(total_support, 3)
            h.contradicting_score = round(total_contra, 3)

            # Evidence Support Score formula
            uncertainty = 0.35
            if total_support > 0 or total_contra > 0:
                raw_conf = total_support / (total_support + 1.25 * total_contra + uncertainty)
            else:
                raw_conf = getattr(h, "prior_prob", 0.25)

            new_conf = round(max(0.05, min(0.98, raw_conf)), 3)
            h.confidence = new_conf

            # 5. State Transitions & Explicit Falsification
            if (round(total_contra, 2) >= 0.90 and total_contra > total_support) or total_contra >= 1.8:
                h.status = "rejected"
                h.net_score = 0.0
                if not h.rejection_reason:
                    h.rejection_reason = f"Contradicted by verified evidence across {len(contradicting_groups)} group(s) (contradiction score: {total_contra:.2f})."
            elif total_contra > 0.0 and total_contra >= total_support * 0.6:
                h.status = "weakened"
                h.net_score = round(max(0.0, total_support - total_contra), 2)
            elif total_support >= 1.3 and total_contra == 0.0:
                h.status = "supported"
                h.net_score = round(max(0.0, total_support - total_contra), 2)
            elif total_support > 0.0:
                h.status = "active"
                h.net_score = round(max(0.0, total_support - total_contra), 2)
            elif h.status == "rejected":
                h.net_score = 0.0
            else:
                # No direct evidence observed yet: retain calibrated prior contribution
                h.status = "unresolved" if h.status not in ["candidate"] else h.status
                h.net_score = round(max(0.05, getattr(h, "prior_prob", 0.25) * 0.50), 2)

            # 6. Audit Confidence Update Logging
            if confidence_history is not None:
                delta = round(new_conf - prev_score, 3)
                if abs(delta) >= 0.01:
                    reason_msg = (
                        f"Corroborated by {num_indep} independent group(s) ({', '.join(supporting_groups)})"
                        if num_indep >= 2 else (
                            f"Supported by single source group ({supporting_groups[0]})" if num_indep == 1 else "No supporting evidence"
                        )
                    )
                    if total_contra > 0:
                        reason_msg += f"; weakened by contradiction in {len(contradicting_groups)} group(s)"

                    update = ConfidenceUpdate(
                        hypothesis_id=h.id,
                        iteration=iteration,
                        previous_score=prev_score,
                        new_score=new_conf,
                        evidence_added=[e for e in h.support_evidence_ids if e in evidence_by_id],
                        support_delta=round(total_support, 3),
                        contradiction_delta=round(total_contra, 3),
                        independent_groups=supporting_groups,
                        reason=reason_msg
                    )
                    confidence_history.append(update)

        # 7. Normalized posterior calculation & Status Rank Assignment
        active_hypo = [h for h in hypotheses if h.status != "rejected"]
        total_net = sum(h.net_score for h in active_hypo) or 1.0
        for h in hypotheses:
            if h.status == "rejected":
                h.posterior_prob = 0.0
            else:
                h.posterior_prob = round(h.net_score / total_net, 3)

        # Enforce sum(posterior_prob) == 1.0 across active hypotheses
        if active_hypo:
            curr_sum = sum(h.posterior_prob for h in active_hypo)
            residual = round(1.0 - curr_sum, 3)
            if abs(residual) > 0:
                best_h = max(active_hypo, key=lambda x: (x.net_score, x.confidence))
                best_h.posterior_prob = round(max(0.0, best_h.posterior_prob + residual), 3)

        # Rank hypotheses: active non-rejected first by net_score descending, then confidence descending
        hypotheses.sort(key=lambda x: (0 if x.status != "rejected" else 1, -x.net_score, -x.confidence))
