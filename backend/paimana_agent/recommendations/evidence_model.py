"""Lineage-aware Evidence Model for candidate recommendation scoring.

Aggregates evidence strength across distinct independence groups to prevent
multiple analytical tools analyzing the same project snapshot from inflating confidence.
"""
from __future__ import annotations
from typing import Any, Optional
from ..evidence.model import Evidence


class CandidateEvidenceModel:
    """Calculates lineage-aware evidence strength for candidate recommendations."""

    def compute_evidence_strength(
        self,
        candidate_evidence_ids: list[str],
        state_evidence_items: list[Evidence],
        contradictions_count: int = 0
    ) -> tuple[float, dict[str, Any]]:
        """Computes lineage-aware evidence strength from cited evidence items."""
        if not candidate_evidence_ids or not state_evidence_items:
            # Fallback for baseline or synthetic review candidates
            base_score = 0.35 if not state_evidence_items else 0.45
            return base_score, {
                "score": base_score,
                "independence_groups": 1,
                "contradictions": contradictions_count,
                "freshness": 1.0,
                "source_authority": 0.50,
                "corroboration_boost": 0.0,
            }

        # Index available evidence
        ev_map = {e.id: e for e in state_evidence_items}
        matched = [ev_map[eid] for eid in candidate_evidence_ids if eid in ev_map]

        if not matched:
            return 0.30, {
                "score": 0.30,
                "independence_groups": 0,
                "contradictions": contradictions_count,
                "freshness": 0.50,
                "source_authority": 0.30,
                "corroboration_boost": 0.0,
                "warning": "No cited evidence IDs matched state evidence items",
            }

        # Partition by independence_group_id
        groups: dict[str, list[Evidence]] = {}
        for ev in matched:
            gid = getattr(ev, "independence_group_id", getattr(ev, "independence_group", "default"))
            groups.setdefault(gid, []).append(ev)

        total_group_strength = 0.0
        for gid, g_items in groups.items():
            primaries = [e for e in g_items if getattr(e, "evidence_type", "direct_observation") != "derived_metric"]
            derived = [e for e in g_items if getattr(e, "evidence_type", "direct_observation") == "derived_metric"]

            if primaries:
                base_str = max(e.calculate_effective_strength() if hasattr(e, "calculate_effective_strength") else getattr(e, "reliability", 1.0) for e in primaries)
            else:
                base_str = max(e.calculate_effective_strength() if hasattr(e, "calculate_effective_strength") else getattr(e, "reliability", 1.0) for e in derived) * 0.70

            derived_contrib = min(0.35, 0.10 * len(derived))
            group_strength = min(1.0, base_str + derived_contrib)
            total_group_strength += group_strength

        # Independent corroboration boost
        num_indep = len(groups)
        corrob_boost = 0.20 * (num_indep - 1) if num_indep >= 2 else 0.0
        raw_strength = total_group_strength + corrob_boost

        # Contradiction penalty
        contra_penalty = min(0.35, 0.15 * contradictions_count)
        net_strength = max(0.10, raw_strength - contra_penalty)

        # Normalize to 0.0 to 1.0 (Single independent group capped at 0.80; 2+ independent groups can reach 1.0)
        if num_indep <= 1:
            normalized_score = round(min(0.80, max(0.05, 0.75 * net_strength)), 3)
        else:
            boosted = 0.80 + min(0.20, 0.10 * (num_indep - 1) + 0.08 * (net_strength / num_indep))
            normalized_score = round(min(1.0, max(0.05, boosted - contra_penalty)), 3)

        mean_fresh = sum(getattr(e, "freshness", 1.0) for e in matched) / len(matched)
        mean_auth = sum(getattr(e, "authority_score", 0.8) for e in matched) / len(matched)

        breakdown = {
            "score": normalized_score,
            "independence_groups": num_indep,
            "group_ids": list(groups.keys()),
            "contradictions": contradictions_count,
            "freshness": round(mean_fresh, 3),
            "source_authority": round(mean_auth, 3),
            "corroboration_boost": round(corrob_boost, 3),
            "contra_penalty": round(contra_penalty, 3),
        }
        return normalized_score, breakdown
