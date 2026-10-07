"""Top-K Peer Ranking and Diversity Optimization Engine.

Ranks eligible candidates by calibrated similarity, enforcing selection limits
while mitigating geographic or agency overconcentration without compromising comparability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..schemas import SimilarityBreakdown


@dataclass
class RankedCandidate:
    """Detailed ranking entry for an evaluated peer candidate."""
    rank: int
    peer_code: str
    peer_name: str
    similarity_score: float
    decision: str  # SELECTED, EXCLUDED_BY_RANK, DIVERSITY_REPLACED
    selection_reason: str
    agency: str
    state: str
    similarity_breakdown: SimilarityBreakdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "peer_code": self.peer_code,
            "peer_name": self.peer_name,
            "similarity_score": round(self.similarity_score, 4),
            "decision": self.decision,
            "selection_reason": self.selection_reason,
            "agency": self.agency,
            "state": self.state,
        }


@dataclass
class RankingResult:
    """Outcome of Top-K ranking with optional diversity optimization."""
    ranked_candidates: List[RankedCandidate]
    selected_peers: List[SimilarityBreakdown]
    diversity_adjustments_made: int
    agency_distribution: Dict[str, int]
    state_distribution: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ranked_candidates": [r.to_dict() for r in self.ranked_candidates],
            "selected_peer_count": len(self.selected_peers),
            "diversity_adjustments_made": self.diversity_adjustments_made,
            "agency_distribution": self.agency_distribution,
            "state_distribution": self.state_distribution,
        }


class PeerRankingEngine:
    """Ranks candidates by similarity score and applies optional diversity guardrails."""

    def rank_and_select(
        self,
        scored_candidates: List[SimilarityBreakdown],
        top_k: int = 10,
        enable_diversity: bool = True,
        max_agency_fraction: float = 0.50,  # Max 50% from a single agency if pool allows
    ) -> RankingResult:
        """Ranks candidates and selects top-K with agency diversity constraints."""
        # 1. Sort strictly by overall similarity
        sorted_candidates = sorted(scored_candidates, key=lambda x: x.overall_similarity, reverse=True)

        if not enable_diversity or len(sorted_candidates) <= top_k:
            selected = sorted_candidates[:top_k]
            ranked_items: List[RankedCandidate] = []
            agency_dist: Dict[str, int] = {}
            state_dist: Dict[str, int] = {}

            for idx, c in enumerate(sorted_candidates, start=1):
                agency = str(c.raw_attributes.get("implementing_agency") or c.raw_attributes.get("agency", "UNKNOWN")).upper()
                state = str(c.raw_attributes.get("state") or c.raw_attributes.get("location", "UNKNOWN")).title()
                is_sel = idx <= top_k

                if is_sel:
                    agency_dist[agency] = agency_dist.get(agency, 0) + 1
                    state_dist[state] = state_dist.get(state, 0) + 1

                ranked_items.append(
                    RankedCandidate(
                        rank=idx,
                        peer_code=c.peer_code,
                        peer_name=c.peer_name,
                        similarity_score=c.overall_similarity,
                        decision="SELECTED" if is_sel else "EXCLUDED_BY_RANK",
                        selection_reason=f"Top {top_k} similarity ranking" if is_sel else f"Beyond top {top_k} limit",
                        agency=agency,
                        state=state,
                        similarity_breakdown=c,
                    )
                )

            return RankingResult(
                ranked_candidates=ranked_items,
                selected_peers=selected,
                diversity_adjustments_made=0,
                agency_distribution=agency_dist,
                state_distribution=state_dist,
            )

        # Diversity-aware greedy selection
        selected_peers: List[SimilarityBreakdown] = []
        ranked_items: List[RankedCandidate] = []
        agency_dist: Dict[str, int] = {}
        state_dist: Dict[str, int] = {}
        adjustments = 0

        max_per_agency = max(1, int(top_k * max_agency_fraction))
        deferred: List[SimilarityBreakdown] = []

        # First pass: fill up to top_k respecting max_per_agency
        for c in sorted_candidates:
            agency = str(c.raw_attributes.get("implementing_agency") or c.raw_attributes.get("agency", "UNKNOWN")).upper()
            curr_agency_count = agency_dist.get(agency, 0)

            if len(selected_peers) < top_k:
                if curr_agency_count < max_per_agency:
                    selected_peers.append(c)
                    agency_dist[agency] = curr_agency_count + 1
                else:
                    deferred.append(c)
                    adjustments += 1
            else:
                deferred.append(c)

        # Second pass: if still under top_k (due to strict agency limits), backfill from deferred
        if len(selected_peers) < top_k and deferred:
            needed = top_k - len(selected_peers)
            for c in deferred[:needed]:
                selected_peers.append(c)
                agency = str(c.raw_attributes.get("implementing_agency") or c.raw_attributes.get("agency", "UNKNOWN")).upper()
                agency_dist[agency] = agency_dist.get(agency, 0) + 1

        selected_codes = {p.peer_code for p in selected_peers}
        for idx, c in enumerate(sorted_candidates, start=1):
            agency = str(c.raw_attributes.get("implementing_agency") or c.raw_attributes.get("agency", "UNKNOWN")).upper()
            state = str(c.raw_attributes.get("state") or c.raw_attributes.get("location", "UNKNOWN")).title()
            is_sel = c.peer_code in selected_codes

            if is_sel:
                state_dist[state] = state_dist.get(state, 0) + 1

            ranked_items.append(
                RankedCandidate(
                    rank=idx,
                    peer_code=c.peer_code,
                    peer_name=c.peer_name,
                    similarity_score=c.overall_similarity,
                    decision="SELECTED" if is_sel else "EXCLUDED_BY_RANK",
                    selection_reason="Selected under diversity constraints" if is_sel else "Excluded by rank or concentration cap",
                    agency=agency,
                    state=state,
                    similarity_breakdown=c,
                )
            )

        return RankingResult(
            ranked_candidates=ranked_items,
            selected_peers=selected_peers,
            diversity_adjustments_made=adjustments,
            agency_distribution=agency_dist,
            state_distribution=state_dist,
        )
