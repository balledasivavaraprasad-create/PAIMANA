"""Hypothesis Lifecycle & Budget Manager.

Orchestrates seeding, dynamic generation triggers, validation, deduplication,
parent-child branching, scoring, and budget enforcement.
"""
from __future__ import annotations
import logging
import time
from typing import Any, Optional
from .model import Hypothesis
from .generator import HypothesisGenerator
from .validator import HypothesisValidator
from .similarity import HypothesisSimilarityChecker
from .scorer import HypothesisScorer

logger = logging.getLogger("paimana_agent.hypotheses.manager")


class HypothesisManager:
    """Manages the full lifecycle of investigation hypotheses."""

    def __init__(
        self,
        generator: Optional[HypothesisGenerator] = None,
        validator: Optional[HypothesisValidator] = None,
        scorer: Optional[HypothesisScorer] = None,
        max_active: int = 6,
        max_generated_per_iteration: int = 2,
        max_total_generated: int = 10
    ):
        self.generator = generator or HypothesisGenerator()
        self.validator = validator or HypothesisValidator()
        self.scorer = scorer or HypothesisScorer()
        self.max_active = max_active
        self.max_generated_per_iteration = max_generated_per_iteration
        self.max_total_generated = max_total_generated
        self.generation_events: list[dict] = []
        self._total_generated_count = 0
        self._total_rejected_count = 0

    def seed_initial_hypotheses(self, event_types: list[str], feats: dict, baseline_evidence: list[Any]) -> list[Hypothesis]:
        """Seeds the initial 4 standard competing causal models."""
        spend_p = 0.40 if "COST_PROGRESS_MISMATCH" in event_types or feats.get("progress_expenditure_gap_pct", 0) > 15 else 0.25
        delay_p = 0.40 if "MILESTONE_DELAYED" in event_types or "PROGRESS_STALLED" in event_types else 0.25
        reg_p = 0.20
        rep_p = 0.15
        total = spend_p + delay_p + reg_p + rep_p
        spend_p, delay_p, reg_p, rep_p = spend_p / total, delay_p / total, reg_p / total, rep_p / total

        fin_ev_ids = [e.id for e in baseline_evidence if "financial" in e.source_tool]
        mile_ev_ids = [e.id for e in baseline_evidence if "milestone" in e.source_tool or "progress" in e.source_tool]

        h1 = Hypothesis(
            id="front_loaded_billing",
            statement="Severe Progress-Expenditure Decoupling: Funds are being drawn or disbursed ahead of commensurate certified physical site delivery.",
            source="seeded",
            status="active",
            confidence=0.55 if spend_p >= delay_p else 0.40,
            prior_prob=spend_p,
            posterior_prob=spend_p,
            support_evidence_ids=fin_ev_ids if spend_p > 0.3 else [],
            predicted_observations=["financial expenditure leads physical completion by >15%", "uncertified contractor advances pending"],
            discriminating_evidence=["disbursement invoices vs PMC technical sign-off books", "bank guarantee ledger"],
            falsification_condition="Independent on-site technical inspection or material audit certifies that actual physical works match cumulative disbursements within 5% tolerance."
        )
        h2 = Hypothesis(
            id="chronic_schedule_delay",
            statement="Chronic Milestone Delay: Structural execution or contractor mobilization bottlenecks have caused extended schedule slippage.",
            source="seeded",
            status="active",
            confidence=0.55 if delay_p > spend_p else 0.40,
            prior_prob=delay_p,
            posterior_prob=delay_p,
            support_evidence_ids=mile_ev_ids if delay_p > 0.3 else [],
            predicted_observations=["milestones overdue > 3 months", "monthly physical progress rate < 1.0%"],
            discriminating_evidence=["monthly contractor labor counts", "critical-path PERT/CPM schedule audit"],
            falsification_condition="Resource-loaded catch-up milestones demonstrate contractor has recovered critical-path schedule slippage with required monthly burn-down rate."
        )
        h3 = Hypothesis(
            id="regulatory_land_clearance",
            statement="Regulatory Clearances & Statutory Bottlenecks: Statutory approvals, RoW, or land acquisition hurdles holding up physical execution.",
            source="seeded",
            status="active",
            confidence=0.30,
            prior_prob=reg_p,
            posterior_prob=reg_p,
            predicted_observations=["environmental or forest clearance pending", "district revenue RoW handover incomplete"],
            discriminating_evidence=["statutory approval portal records", "revenue department land acquisition awards"],
            falsification_condition="State revenue department and environmental regulatory portals confirm 100% encumbrance-free Right-of-Way (RoW) and statutory stage-2 approvals are formally in hand."
        )
        h4 = Hypothesis(
            id="reporting_discrepancy",
            statement="MPR Data Inconsistency / Reporting Lag: Data lag or administrative discrepancy between certified progress and milestone schedule.",
            source="seeded",
            status="active",
            confidence=0.20,
            prior_prob=rep_p,
            posterior_prob=rep_p,
            predicted_observations=["reported milestone dates inconsistent with site measurement books", "zero slippage reported despite stalled civil works"],
            discriminating_evidence=["field engineer site measurement books", "audit reconciliation between portal and ground reality"],
            falsification_condition="Cross-reconciliation of field engineer physical progress books and online MPR records proves data entry consistency with zero lag."
        )
        return [h1, h2, h3, h4]

    def process_iteration(
        self,
        hypotheses: list[Hypothesis],
        evidence_items: list[Any],
        unexplained_evidence: list[Any],
        has_contradictions: bool,
        project_context: dict,
        iteration: int,
        converged: bool = False,
        confidence_history: Optional[list[Any]] = None
    ) -> list[Hypothesis]:
        """Evaluates hypotheses against evidence, generates candidates if needed, and applies budget constraints."""
        # 1. Update scores and state transitions of existing hypotheses
        self.scorer.score_and_transition(hypotheses, evidence_items, iteration, confidence_history=confidence_history)

        # 2. Check if hypothesis generation is triggered
        active_hypo = [h for h in hypotheses if h.status in ["active", "supported", "candidate", "PRIMARY", "COMPETING", "unresolved"]]
        should_gen, trigger_reason = self.generator.should_generate(
            unexplained_evidence, active_hypo, has_contradictions, iteration, converged
        )

        if should_gen and self._total_generated_count < self.max_total_generated:
            logger.info(f"[Hypothesis Generation Triggered] {trigger_reason}")
            candidates = self.generator.generate_candidates(
                unexplained_evidence=unexplained_evidence,
                active_hypotheses=hypotheses,
                project_context=project_context,
                iteration=iteration,
                max_candidates=self.max_generated_per_iteration
            )

            known_eids = {e.id for e in evidence_items}
            known_claims = [e.claim for e in evidence_items]

            for cand in candidates:
                self._total_generated_count += 1
                is_valid, reason, merged_id = self.validator.validate_candidate(
                    candidate=cand,
                    known_evidence_ids=known_eids,
                    known_evidence_claims=known_claims,
                    existing_hypotheses=hypotheses
                )

                # Record generation event for auditable Langfuse/Tracer logging
                event_record = {
                    "hypothesis_id": cand.id,
                    "statement": cand.statement,
                    "generated_at_iteration": iteration,
                    "trigger": trigger_reason,
                    "evidence_that_triggered_generation": [e.id for e in unexplained_evidence],
                    "parent_hypothesis_id": cand.parent_hypothesis_id,
                    "generation_model": "LLM" if self.generator.enabled else "DeterministicDomainSynthesis",
                    "accepted": is_valid,
                    "validation_result": reason,
                    "merged_with_id": merged_id,
                    "timestamp": time.time(),
                }
                self.generation_events.append(event_record)

                if is_valid:
                    cand.status = "active"
                    hypotheses.append(cand)
                    logger.info(f"Accepted novel hypothesis '{cand.id}': {cand.statement}")
                else:
                    self._total_rejected_count += 1
                    logger.warning(f"Rejected candidate hypothesis '{cand.id}': {reason}")
                    if merged_id:
                        # Append evidence references to merged existing hypothesis
                        match = next((h for h in hypotheses if h.id == merged_id), None)
                        if match:
                            for eid in cand.support_evidence_ids:
                                if eid not in match.support_evidence_ids:
                                    match.support_evidence_ids.append(eid)

            # Re-score with new candidates included
            self.scorer.score_and_transition(hypotheses, evidence_items, iteration, confidence_history=confidence_history)

        # 3. Enforce active budget constraints
        self._enforce_budget(hypotheses)

        return hypotheses

    def branch_hypothesis(
        self,
        parent_id: str,
        child_id: str,
        child_statement: str,
        predicted_observations: list[str],
        discriminating_evidence: list[str],
        hypotheses: list[Hypothesis],
        iteration: int
    ) -> Optional[Hypothesis]:
        """Creates a specialized child hypothesis refining a broader parent hypothesis."""
        parent = next((h for h in hypotheses if h.id == parent_id), None)
        if not parent:
            return None

        child = Hypothesis(
            id=child_id,
            statement=child_statement,
            source="agent_generated",
            status="active",
            parent_hypothesis_id=parent_id,
            predicted_observations=predicted_observations,
            discriminating_evidence=discriminating_evidence,
            created_at_iteration=iteration,
            last_updated_iteration=iteration,
            support_evidence_ids=list(parent.support_evidence_ids),
            confidence=parent.confidence,
            falsification_condition=f"Field audit disproves specialized mechanism: {child_statement}"
        )
        hypotheses.append(child)
        self.generation_events.append({
            "hypothesis_id": child.id,
            "statement": child.statement,
            "generated_at_iteration": iteration,
            "trigger": f"Branching refinement from parent '{parent_id}'",
            "parent_hypothesis_id": parent_id,
            "accepted": True,
            "validation_result": "Passed (Refinement branch)",
            "timestamp": time.time(),
        })
        return child

    def falsify_hypothesis(
        self,
        hypothesis_id: str,
        contradicting_evidence: Any,
        reason: str,
        hypotheses: list[Hypothesis]
    ) -> Optional[Hypothesis]:
        """Explicitly falsifies a hypothesis upon receiving definitive contradictory evidence."""
        target = next((h for h in hypotheses if h.id == hypothesis_id), None)
        if not target:
            return None
        target.status = "rejected"
        target.rejection_reason = reason
        if hasattr(contradicting_evidence, "id"):
            if contradicting_evidence.id not in target.contradiction_evidence_ids:
                target.contradiction_evidence_ids.append(contradicting_evidence.id)
        target.net_score = 0.0
        target.posterior_prob = 0.0
        return target

    def _enforce_budget(self, hypotheses: list[Hypothesis]) -> None:
        """Prunes excessive candidate/unresolved hypotheses if active count exceeds max_active."""
        active = [h for h in hypotheses if h.status in ["active", "candidate", "unresolved", "PRIMARY", "COMPETING", "supported"]]
        if len(active) > self.max_active:
            # Sort active by confidence descending, keep top max_active, demote rest to weakened
            active.sort(key=lambda h: h.confidence, reverse=True)
            for h in active[self.max_active:]:
                h.status = "weakened"
                if not h.rejection_reason:
                    h.rejection_reason = "Pruned due to hypothesis budget constraints (lower relative confidence)."
