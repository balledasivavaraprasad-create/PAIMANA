"""Multidimensional Investigation Convergence Engine.

Coordinates multi-dimensional evaluations across evidence coverage, hypothesis separation,
stability, contradictions, causal support, decision readiness, and marginal information gain.
Replaces fixed iteration loops with scientifically defensible convergence management.
"""
from __future__ import annotations
from typing import Any, Optional

from .models import ConvergenceState, ConvergenceStatus, TerminationRecord
from .convergence_policy import ConvergencePolicy
from .evidence_coverage import EvidenceCoverageEvaluator
from .hypothesis_separation import HypothesisSeparationEvaluator
from .hypothesis_stability import HypothesisStabilityEvaluator
from .contradiction_resolution import ContradictionResolutionEvaluator
from .causal_convergence import CausalConvergenceEvaluator
from .decision_readiness import DecisionReadinessEvaluator
from .diminishing_returns import DiminishingReturnsDetector
from .saturation import EvidenceSaturationDetector
from .oscillation import HypothesisOscillationDetector
from .termination_trace import TerminationTraceBuilder


class ConvergenceEngine:
    """Master convergence evaluation engine."""

    def __init__(self, policy: Optional[ConvergencePolicy] = None):
        self.policy = policy or ConvergencePolicy()
        self.gain_history: list[float] = []
        self.leader_history: list[str] = []
        self.margin_history: list[float] = []
        self.hypothesis_snapshots: list[dict[str, float]] = []

    def evaluate(
        self,
        state: Any,
        candidates: list[Any],
        open_needs: Optional[list[Any]] = None,
        budget: Optional[Any] = None,
        iteration: int = 0
    ) -> tuple[ConvergenceState, Optional[TerminationRecord]]:
        """Executes full two-stage multidimensional convergence evaluation."""
        # 1. Dimension Evaluations
        # A. Evidence Coverage
        cov_res = EvidenceCoverageEvaluator.evaluate_coverage(state, open_needs)
        evidence_coverage = cov_res["evidence_coverage"]

        # B. Hypothesis Separation
        hypotheses = getattr(state, "hypotheses", [])
        sep_res = HypothesisSeparationEvaluator.evaluate_separation(hypotheses)
        hypothesis_separation = sep_res["hypothesis_separation"]
        leader_id = sep_res["leading_id"]
        margin = sep_res["margin"]
        if leader_id:
            self.leader_history.append(leader_id)
            self.margin_history.append(margin)

        # C. Hypothesis Stability
        current_scores = {}
        for i, h in enumerate(hypotheses):
            h_key = getattr(h, "id", None) or getattr(h, "name", None) or getattr(h, "title", f"H{i}")
            h_score = getattr(h, "confidence_score", getattr(h, "confidence", 0.0))
            if isinstance(h_score, str):
                h_score = 0.85 if h_score.upper() == "HIGH" else (0.50 if h_score.upper() == "MEDIUM" else 0.20)
            current_scores[h_key] = float(h_score)
            if hasattr(h, "name") and h.name:
                current_scores[h.name] = float(h_score)
            if hasattr(h, "id") and h.id:
                current_scores[h.id] = float(h_score)

        stab_res = HypothesisStabilityEvaluator.evaluate_stability(
            self.hypothesis_snapshots, current_scores,
            stability_threshold=0.05,
            required_stable_steps=self.policy.min_consecutive_stable_steps
        )
        self.hypothesis_snapshots.append(current_scores)
        hypothesis_stability = stab_res["hypothesis_stability"]

        # D. Contradiction Resolution
        contradictions = getattr(state, "contradictions", [])
        contra_res = ContradictionResolutionEvaluator.evaluate_contradictions(contradictions)
        contradiction_resolution = contra_res["contradiction_resolution"]
        has_blocking_contra = contra_res["has_blocking_contradictions"]

        # E. Causal Support
        causal_res = CausalConvergenceEvaluator.evaluate_causal_convergence(state)
        causal_support = causal_res["causal_support"]

        # F. Decision Readiness
        read_res = DecisionReadinessEvaluator.evaluate_readiness(state, causal_support, candidates)
        decision_readiness = read_res["decision_readiness"]

        # G. Eligible Tools and Expected Information Gain
        eligible_cands = [c for c in candidates if getattr(c, "eligible", True)]
        best_cand = eligible_cands[0] if eligible_cands else None
        best_gain = getattr(best_cand, "expected_information_gain", 0.0) if best_cand else 0.0

        # Marginal realized gain from previous step
        realized_gain = 0.0
        if len(self.hypothesis_snapshots) >= 2:
            prev = self.hypothesis_snapshots[-2]
            curr = self.hypothesis_snapshots[-1]
            realized_gain = max(0.0, sum(abs(curr.get(k, 0.0) - prev.get(k, 0.0)) for k in curr) / max(1, len(curr)))
        self.gain_history.append(realized_gain)

        # Diminishing Returns & Saturation Checks
        dim_res = DiminishingReturnsDetector.evaluate_trend(self.gain_history, window=self.policy.diminishing_returns_window, threshold=self.policy.diminishing_returns_threshold)
        sat_res = EvidenceSaturationDetector.detect_saturation(state, getattr(state, "tool_executions", []))
        osc_res = HypothesisOscillationDetector.detect_oscillation(self.leader_history, self.margin_history)

        # --------------------------------------------------------------------
        # Stage 1: Resource & Safety Boundaries (Hard Limits)
        # --------------------------------------------------------------------
        if budget is not None and getattr(budget, "is_exhausted", lambda: False)():
            status = ConvergenceStatus.BUDGET_EXHAUSTED
            term_reason = ConvergenceStatus.TOOL_LIMIT_REACHED
            used_calls = max(getattr(budget, "tool_calls_used", 0), getattr(getattr(budget, "consumed", None), "tool_calls", 0))
            explanation = f"Hard safety boundary reached: budget exhausted ({used_calls}/{budget.max_tool_calls} calls)."

            # Apply confidence coupling to state
            try:
                from ...governance.budget import GracefulDegradationManager, DegradationLevel
                state.degradation_level = DegradationLevel.LEVEL_4_SAFE_TERMINATION.value
                coup = GracefulDegradationManager.apply_confidence_coupling(
                    DegradationLevel.LEVEL_4_SAFE_TERMINATION,
                    getattr(state, "confidence_score", 0.5),
                    evidence_coverage
                )
                if hasattr(state, "confidence_reasons") and isinstance(state.confidence_reasons, list):
                    for cav in coup.get("caveats", []):
                        if cav not in state.confidence_reasons:
                            state.confidence_reasons.append(cav)
            except Exception:
                pass

            conv_state = ConvergenceState(
                evidence_coverage=evidence_coverage,
                hypothesis_separation=hypothesis_separation,
                hypothesis_stability=hypothesis_stability,
                contradiction_resolution=contradiction_resolution,
                causal_support=causal_support,
                decision_readiness=decision_readiness,
                marginal_information_gain=realized_gain,
                expected_information_gain=best_gain,
                unresolved_material_questions=contra_res["unresolved_count"],
                remaining_high_value_tools=len(eligible_cands),
                status=status,
                termination_reason=term_reason,
                should_terminate=True,
                explanation=explanation,
                iteration=iteration,
            )
            term_record = TerminationTraceBuilder.build_termination_record(conv_state, best_cand, iteration, used_calls, self.policy.minimum_useful_gain)
            return conv_state, term_record

        # --------------------------------------------------------------------
        # Stage 2: Multidimensional Convergence & Terminal States
        # --------------------------------------------------------------------
        max_utility = max([getattr(c, "net_utility", 0.0) for c in eligible_cands], default=0.0)
        min_util_thresh = getattr(budget, "min_utility_threshold", 0.15) if budget else 0.15

        # Check blocking contradictions
        if has_blocking_contra:
            # If an eligible tool exists with expected gain >= threshold, keep investigating to resolve!
            if best_gain >= self.policy.minimum_useful_gain and eligible_cands:
                status = ConvergenceStatus.PROGRESSING
                should_terminate = False
                term_reason = None
                explanation = f"Active high/critical contradictions detected ({contra_res['resolution_notes']}). Continuing investigation to resolve discrepancy."
            else:
                status = ConvergenceStatus.CONTRADICTORY
                should_terminate = True
                term_reason = "CONTRADICTORY_EVIDENCE"
                explanation = f"Investigation blocked by unresolved high/critical contradictions ({contra_res['resolution_notes']}). No remaining tools available to resolve conflict."

        # Check full convergence conditions
        elif (
            evidence_coverage >= self.policy.min_evidence_coverage
            and hypothesis_separation >= self.policy.min_hypothesis_separation
            and hypothesis_stability >= self.policy.min_hypothesis_stability
            and contradiction_resolution >= self.policy.min_contradiction_resolution
            and causal_support >= self.policy.min_causal_support
            and decision_readiness >= self.policy.min_decision_readiness
            and not has_blocking_contra
            and not osc_res["is_oscillating"]
            and len(getattr(state, "tools_used", [])) >= 2
        ):
            status = ConvergenceStatus.CONVERGED
            should_terminate = True
            term_reason = "SUFFICIENT_EVIDENCE"
            explanation = (
                f"Investigation converged across all dimensions: Evidence coverage ({evidence_coverage*100:.0f}%), "
                f"Hypothesis separation ({hypothesis_separation*100:.0f}%), Stability ({hypothesis_stability*100:.0f}%), "
                f"Causal support ({causal_support*100:.0f}%), Contradictions resolved (100%)."
            )

        # Check evidence saturation or diminishing returns with low expected gain
        elif (sat_res["is_saturated"] or dim_res["has_diminishing_returns"]) and (best_gain < self.policy.minimum_useful_gain):
            status = ConvergenceStatus.NO_HIGH_VALUE_EVIDENCE_AVAILABLE
            should_terminate = True
            term_reason = "NO_HIGH_VALUE_TOOL_REMAINING"
            explanation = sat_res["saturation_rationale"] or f"Diminishing returns reached: incremental information gains flattened ({dim_res['mean_recent_gain']:.3f} < {self.policy.diminishing_returns_threshold})."

        elif not eligible_cands:
            if evidence_coverage < 0.50 and open_needs:
                status = ConvergenceStatus.INSUFFICIENT_EVIDENCE
                should_terminate = True
                term_reason = "INSUFFICIENT_EVIDENCE"
                explanation = f"Evidence coverage insufficient ({evidence_coverage*100:.0f}%), but no eligible tools remain in registry."
            else:
                status = ConvergenceStatus.NO_HIGH_VALUE_EVIDENCE_AVAILABLE
                should_terminate = True
                term_reason = "NO_HIGH_VALUE_TOOL_REMAINING"
                explanation = "No eligible tools available to gather additional evidence."

        elif best_gain < self.policy.minimum_useful_gain or max_utility < min_util_thresh:
            if not open_needs and len(getattr(state, "tools_used", [])) >= 2:
                status = ConvergenceStatus.NO_HIGH_VALUE_EVIDENCE_AVAILABLE
                should_terminate = True
                term_reason = "NO_HIGH_VALUE_TOOL_REMAINING"
                explanation = f"All open needs resolved. Remaining tool utility ({max_utility:.3f}) falls below threshold ({min_util_thresh}). Stopping to prevent wasteful execution."
            elif evidence_coverage < 0.40 and open_needs:
                status = ConvergenceStatus.INSUFFICIENT_EVIDENCE
                should_terminate = True
                term_reason = "INSUFFICIENT_EVIDENCE"
                explanation = f"Evidence coverage poor ({evidence_coverage*100:.0f}%), but all remaining tools fall below utility threshold ({max_utility:.3f} < {min_util_thresh})."
            else:
                status = ConvergenceStatus.NO_HIGH_VALUE_EVIDENCE_AVAILABLE
                should_terminate = True
                term_reason = "NO_HIGH_VALUE_TOOL_REMAINING"
                explanation = f"Remaining tool utility ({max_utility:.3f}) falls below worthwhile threshold ({min_util_thresh}). Stopping to prevent wasteful execution."

        else:
            # Active investigation continuing
            # Calculate how close to convergence
            met_criteria = sum([
                evidence_coverage >= self.policy.min_evidence_coverage,
                hypothesis_separation >= self.policy.min_hypothesis_separation,
                hypothesis_stability >= self.policy.min_hypothesis_stability,
                contradiction_resolution >= self.policy.min_contradiction_resolution,
                causal_support >= self.policy.min_causal_support,
                decision_readiness >= self.policy.min_decision_readiness,
            ])
            status = ConvergenceStatus.NEAR_CONVERGED if met_criteria >= 4 else ConvergenceStatus.PROGRESSING
            should_terminate = False
            term_reason = None
            explanation = f"Investigation actively progressing ({met_criteria}/6 convergence criteria met). Next best tool: '{best_cand.tool_name}' (expected gain={best_gain:.3f})."

        conv_state = ConvergenceState(
            evidence_coverage=evidence_coverage,
            hypothesis_separation=hypothesis_separation,
            hypothesis_stability=hypothesis_stability,
            contradiction_resolution=contradiction_resolution,
            causal_support=causal_support,
            decision_readiness=decision_readiness,
            marginal_information_gain=realized_gain,
            expected_information_gain=best_gain,
            unresolved_material_questions=contra_res["unresolved_count"],
            remaining_high_value_tools=len(eligible_cands),
            status=status,
            termination_reason=term_reason,
            should_terminate=should_terminate,
            explanation=explanation,
            iteration=iteration,
            dimension_scores={
                "coverage": evidence_coverage,
                "separation": hypothesis_separation,
                "stability": hypothesis_stability,
                "contradictions": contradiction_resolution,
                "causal": causal_support,
                "readiness": decision_readiness,
            }
        )

        term_record = None
        if should_terminate:
            calls_used = getattr(budget, "tool_calls_used", len(getattr(state, "tools_used", [])))
            term_record = TerminationTraceBuilder.build_termination_record(
                conv_state, best_cand, iteration, calls_used, self.policy.minimum_useful_gain
            )

        return conv_state, term_record
