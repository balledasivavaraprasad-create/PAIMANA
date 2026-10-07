"""Adaptive Cohort Sizing & Controlled Relaxation Engine.

Ensures cohorts achieve analytical validity without relaxing non-negotiable
eligibility rules (temporal safety, non-identity). Generates a complete audit trail
of any threshold or parameter relaxations performed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..schemas import SimilarityBreakdown
from .context import PeerInvestigationContext
from .strategy_registry import PeerStrategyDefinition


@dataclass
class RelaxationStep:
    """Audit record capturing a single parameter relaxation."""
    step_number: int
    parameter: str
    original_value: Any
    relaxed_value: Any
    reason: str
    additional_peers_found: int
    cohort_size_after: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "parameter": self.parameter,
            "original_value": self.original_value,
            "relaxed_value": self.relaxed_value,
            "reason": self.reason,
            "additional_peers_found": self.additional_peers_found,
            "cohort_size_after": self.cohort_size_after,
        }


@dataclass
class AdaptiveCohortResult:
    """Outcome of adaptive cohort selection including complete audit trail."""
    selected_peers: List[SimilarityBreakdown]
    initial_peer_count: int
    final_peer_count: int
    was_relaxed: bool
    relaxation_history: List[RelaxationStep] = field(default_factory=list)
    quality_status: str = "SUFFICIENT"
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_peer_codes": [p.peer_code for p in self.selected_peers],
            "initial_peer_count": self.initial_peer_count,
            "final_peer_count": self.final_peer_count,
            "was_relaxed": self.was_relaxed,
            "relaxation_history": [r.to_dict() for r in self.relaxation_history],
            "quality_status": self.quality_status,
            "summary": self.summary,
        }


class AdaptiveCohortSelector:
    """Progressively selects peers, applying controlled relaxation if pool is insufficient."""

    def select_cohort(
        self,
        scored_candidates: List[SimilarityBreakdown],
        strategy: PeerStrategyDefinition,
        context: Optional[PeerInvestigationContext] = None,
        min_cohort_size: int = 3,
        target_cohort_size: int = 10,
    ) -> AdaptiveCohortResult:
        """Selects peers with adaptive threshold relaxation if candidate count is below min_cohort_size."""
        # Sort candidates descending by overall similarity
        ranked = sorted(scored_candidates, key=lambda x: x.overall_similarity, reverse=True)

        initial_threshold = context.min_similarity if context else strategy.min_similarity_threshold
        allow_relaxation = context.allow_relaxation if context else True

        # Initial filtering
        current_peers = [c for c in ranked if c.overall_similarity >= initial_threshold]
        initial_count = len(current_peers)
        relaxation_history: List[RelaxationStep] = []

        if initial_count >= min_cohort_size or not allow_relaxation:
            selected = current_peers[:target_cohort_size]
            status = "SUFFICIENT" if len(selected) >= min_cohort_size else "INSUFFICIENT"
            return AdaptiveCohortResult(
                selected_peers=selected,
                initial_peer_count=initial_count,
                final_peer_count=len(selected),
                was_relaxed=False,
                relaxation_history=[],
                quality_status=status,
                summary=f"Selected {len(selected)} peers at initial similarity threshold {initial_threshold}.",
            )

        # Apply controlled relaxation in controlled stages
        current_threshold = initial_threshold
        step_idx = 1

        # Stage 1: Lower similarity threshold by 0.10 (down to minimum 0.40)
        relaxed_thresh = max(0.40, initial_threshold - 0.10)
        new_peers = [c for c in ranked if c.overall_similarity >= relaxed_thresh]
        additional = len(new_peers) - len(current_peers)

        relaxation_history.append(
            RelaxationStep(
                step_number=step_idx,
                parameter="min_similarity_threshold",
                original_value=round(current_threshold, 2),
                relaxed_value=round(relaxed_thresh, 2),
                reason=f"Initial threshold yielded only {len(current_peers)} peers (below minimum {min_cohort_size}).",
                additional_peers_found=additional,
                cohort_size_after=len(new_peers),
            )
        )
        current_peers = new_peers
        current_threshold = relaxed_thresh
        step_idx += 1

        # Stage 2: If still below min_cohort_size, allow threshold down to 0.35
        if len(current_peers) < min_cohort_size:
            stage2_thresh = 0.35
            stage2_peers = [c for c in ranked if c.overall_similarity >= stage2_thresh]
            additional2 = len(stage2_peers) - len(current_peers)
            relaxation_history.append(
                RelaxationStep(
                    step_number=step_idx,
                    parameter="min_similarity_threshold",
                    original_value=round(current_threshold, 2),
                    relaxed_value=round(stage2_thresh, 2),
                    reason="Second relaxation stage to achieve minimum analytical baseline.",
                    additional_peers_found=additional2,
                    cohort_size_after=len(stage2_peers),
                )
            )
            current_peers = stage2_peers
            current_threshold = stage2_thresh

        selected = current_peers[:target_cohort_size]
        status = "SUFFICIENT" if len(selected) >= min_cohort_size else "INSUFFICIENT"
        summary = (
            f"Adaptive selection: {len(selected)} peers obtained after {len(relaxation_history)} relaxation step(s) "
            f"(threshold relaxed from {initial_threshold} to {current_threshold})."
        )

        return AdaptiveCohortResult(
            selected_peers=selected,
            initial_peer_count=initial_count,
            final_peer_count=len(selected),
            was_relaxed=True,
            relaxation_history=relaxation_history,
            quality_status=status,
            summary=summary,
        )
