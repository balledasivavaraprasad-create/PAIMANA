"""Candidate Generator producing 5-10 structured recommendation candidates across 5 distinct sources."""
from __future__ import annotations
import logging
from typing import Any, Optional
from .candidate import RecommendationCandidate

logger = logging.getLogger("paimana_agent.recommendations.candidate_generator")


class CandidateGenerator:
    """Generates structured recommendation candidates from hypotheses, evidence, precedents, playbooks, and LLM."""

    def generate_candidates(
        self,
        leading_hypotheses: list[Any],
        investigation_outcome: str,
        project: dict,
        feats: dict,
        precedents: dict,
        investigation_state: Optional[Any] = None,
        llm_client: Optional[Any] = None
    ) -> list[RecommendationCandidate]:
        """Generates 5-10 candidate recommendations across 5 sources."""
        cost = float(project.get("original_cost_cr", 0.0))
        is_mega = cost >= 1000.0 or feats.get("is_mega_project", False)
        succ = precedents.get("successful_precedents", [])
        candidates: list[RecommendationCandidate] = []

        top_h = leading_hypotheses[0] if leading_hypotheses else None
        top_id = getattr(top_h, "id", getattr(top_h, "name", "")).lower() if top_h else ""
        top_conf = getattr(top_h, "confidence", 0.0)
        top_status = getattr(top_h, "status", "").lower()

        # Collect available state evidence IDs for clean attribution
        ev_items = getattr(investigation_state, "evidence_items", [])
        state_ev_ids = [e.id for e in ev_items]
        primary_ev_ids = [e.id for e in ev_items if getattr(e, "evidence_type", "direct_observation") != "derived_metric"] or state_ev_ids

        # --------------------------------------------------------------------
        # Source 1: Historical Precedent / Memory Candidate
        # --------------------------------------------------------------------
        supporting = precedents.get("supporting_precedents", [])
        if (succ or supporting) and top_conf >= 0.40:
            if succ:
                p_action = succ[0].get("action", "")
                p_outcome = succ[0].get("outcome", "")
                p_code = succ[0].get("project_code", "HIST-1")
            else:
                top_sup = supporting[0] if isinstance(supporting[0], dict) else supporting[0].to_dict()
                p_action = top_sup.get("intervention", {}).get("action", "") or top_sup.get("title", "")
                p_outcome = str(top_sup.get("observed_outcome", {}).get("notes", "") or top_sup.get("observed_outcome", {}).get("status", "positive recovery"))
                p_code = top_sup.get("source_project_id") or top_sup.get("id", "HIST-1")
            candidates.append(RecommendationCandidate(
                id=f"REC-PRE-{len(candidates)+1:02d}",
                title=f"Implement verified recovery measure: '{p_action[:60]}'. (Validated by prior positive outcome: '{p_outcome[:70]}').",
                action_type="PRIMARY_RECOVERY",
                description=f"Replicate empirically validated recovery measure from historical project {p_code}.",
                rationale=f"Directly informed by historical success on project {p_code} where this action resolved similar anomalies.",
                hypothesis_ids=[top_id] if top_id else [],
                evidence_ids=primary_ev_ids[:2],
                expected_benefit=0.88,
                expected_cost=0.35,
                expected_risk_reduction=0.82,
                implementation_risk=0.18,
                authority_score=0.90,
                responsible_stakeholder="Project Director & Ministry Infrastructure Monitoring Division",
                urgency="HIGH",
                approval_class="executive" if is_mega else "managerial",
                tradeoffs="Requires dedicated monitoring overhead; execution contingent on implementing agency adherence.",
                risks="Potential coordination resistance from field contractors during initial transition.",
                uncertainty="LOW",
                precedent_outcome=p_outcome,
                expected_impact="High probability of operational recovery based on empirical historical success",
                generated_by="precedent_memory"
            ))

        # --------------------------------------------------------------------
        # Source 2: Outcome-Calibrated Recommendations
        # --------------------------------------------------------------------
        if investigation_outcome == "INSUFFICIENT_EVIDENCE" or (top_conf < 0.35 and top_status != "supported"):
            candidates.append(RecommendationCandidate(
                id=f"REC-EXP-{len(candidates)+1:02d}",
                title="Deploy Joint Fact-Finding Technical Inspection to collect targeted on-site measurements and resolve open evidence gaps.",
                action_type="FORENSIC_AUDIT",
                description="Multi-disciplinary engineering inspection team dispatched to ground zero.",
                rationale="Current observations are insufficient to confirm a single dominant root cause; independent on-site ground data required.",
                hypothesis_ids=[top_id] if top_id else [],
                evidence_ids=[f"Top hypothesis '{top_id}' confidence is preliminary ({top_conf:.2f})."],
                expected_benefit=0.74,
                expected_cost=0.28,
                expected_risk_reduction=0.70,
                implementation_risk=0.15,
                authority_score=0.88,
                responsible_stakeholder="Superintending Engineer & PMU Technical Auditor",
                urgency="MEDIUM",
                approval_class="managerial",
                tradeoffs="Defers major contract interventions by 15-20 days pending physical site audit.",
                risks="Slight administrative delay in executing punitive contractual measures.",
                uncertainty="HIGH",
                expected_impact="Eliminates diagnostic ambiguity and prevents premature or wrongful contractual penalties",
                generated_by="playbook"
            ))
        elif investigation_outcome == "MULTIPLE_PLAUSIBLE_CAUSES":
            candidates.append(RecommendationCandidate(
                id=f"REC-MUL-{len(candidates)+1:02d}",
                title="Convene Multi-Disciplinary Steering Committee to address compound execution and statutory bottlenecks simultaneously.",
                action_type="PRIMARY_RECOVERY",
                description="Establish unified inter-departmental taskforce to unblock overlapping constraints.",
                rationale="Project exhibits compound risk drivers across multiple independent operational dimensions.",
                hypothesis_ids=[h.id for h in leading_hypotheses[:2]],
                evidence_ids=primary_ev_ids[:2],
                expected_benefit=0.80,
                expected_cost=0.30,
                expected_risk_reduction=0.75,
                implementation_risk=0.20,
                authority_score=0.90,
                responsible_stakeholder="Joint Secretary (Infrastructure) & Chief Engineer",
                urgency="HIGH",
                approval_class="executive",
                tradeoffs="Requires coordinated multi-agency alignment across distinct ministry departments.",
                risks="Diffusion of immediate accountability across working groups.",
                uncertainty="MEDIUM",
                expected_impact="Establishes unified inter-departmental taskforce to unblock overlapping constraints",
                generated_by="playbook"
            ))
        # Domain-Specific Playbooks
        if "billing" in top_id or "decoupling" in top_id or "cost_progress" in str(getattr(investigation_state, "triggering_events", [])):
            candidates.append(RecommendationCandidate(
                id=f"REC-PBK-{len(candidates)+1:02d}",
                title="Establish Joint Financial-Physical Audit Taskforce to reconcile certified physical milestones against contractor mobilization invoices prior to next installment release.",
                action_type="FORENSIC_AUDIT",
                description="Convene an independent financial-physical audit taskforce to reconcile unverified contractor disbursements.",
                rationale="Sanctioned disbursements are advancing significantly faster than certified on-site works.",
                hypothesis_ids=[top_id] if top_id else ["financial_billing_decoupling"],
                evidence_ids=[eid for eid in state_ev_ids if "financial" in eid or "spend" in eid or "delay" in eid] or primary_ev_ids[:2],
                expected_benefit=0.86,
                expected_cost=0.30,
                expected_risk_reduction=0.85,
                implementation_risk=0.22,
                authority_score=0.92,
                responsible_stakeholder="Ministry Financial Advisor & Chief Engineer" if is_mega else "Project Director & Superintending Engineer",
                urgency="CRITICAL" if is_mega else "HIGH",
                approval_class="executive",
                tradeoffs="Freezes interim contractor disbursements until reconciliation; may create short-term mobilization pause.",
                risks="Contractor claim for equipment idle charges if reconciliation exceeds 30 calendar days.",
                uncertainty="LOW",
                expected_impact="Freezes unverified expenditure and ensures strict milestone linkage",
                generated_by="playbook"
            ))

        if "delay" in top_id or "schedule" in top_id or "procurement" in top_id or "contractor" in top_id:
            candidates.append(RecommendationCandidate(
                id=f"REC-PBK-{len(candidates)+1:02d}",
                title="Require executing agency to submit a resource-loaded Catch-Up Schedule with fortnightly milestone check-ins.",
                action_type="RECOVERY_PLAN",
                description="Mandate a resource-loaded catch-up program with fortnightly physical verification gates.",
                rationale="Critical path execution slippage exceeds contractual milestones.",
                hypothesis_ids=[top_id] if top_id else ["chronic_schedule_delay"],
                evidence_ids=[eid for eid in state_ev_ids if "milestone" in eid or "delay" in eid or "schedule" in eid] or primary_ev_ids[:2],
                expected_benefit=0.82,
                expected_cost=0.25,
                expected_risk_reduction=0.76,
                implementation_risk=0.20,
                authority_score=0.88,
                responsible_stakeholder="Executive Director (Projects) & Chief Engineer",
                urgency="HIGH",
                approval_class="managerial",
                tradeoffs="Focuses solely on existing contractor resources without capital infusion or scope reduction.",
                risks="Superficial schedule re-baselining without addressing structural labor or supply shortages.",
                uncertainty="MEDIUM",
                expected_impact="Re-establishes milestone accountability and clears contractor bottlenecks",
                generated_by="playbook"
            ))

        if "clearance" in top_id or "land" in top_id or "regulatory" in top_id:
            candidates.append(RecommendationCandidate(
                id=f"REC-PBK-{len(candidates)+1:02d}",
                title="Escalate RoW encumbrances and pending statutory environmental approvals to State Chief Secretary Apex Committee.",
                action_type="ESCALATION",
                description="Escalate statutory clearance bottlenecks to state apex governance level.",
                rationale="Statutory Stage-2 environmental clearances or RoW land handovers are holding up site mobilization.",
                hypothesis_ids=[top_id] if top_id else ["regulatory_land_clearance"],
                evidence_ids=primary_ev_ids[:2],
                expected_benefit=0.84,
                expected_cost=0.20,
                expected_risk_reduction=0.78,
                implementation_risk=0.25,
                authority_score=0.95,
                responsible_stakeholder="Ministry Nodal Officer & State Infrastructure Secretary",
                urgency="HIGH",
                approval_class="statutory",
                tradeoffs="Requires state-level executive intervention outside project implementing agency.",
                risks="State political negotiation delays.",
                uncertainty="LOW",
                expected_impact="Resolves land handover blocks and unlocks encumbrance-free construction fronts",
                generated_by="playbook"
            ))

        # --------------------------------------------------------------------
        # Source 3: Hypothesis-Driven Multi-Tier Actions
        # --------------------------------------------------------------------
        # A. Monitoring frequency escalation
        candidates.append(RecommendationCandidate(
            id=f"REC-HYP-{len(candidates)+1:02d}",
            title="Institute weekly intensive engineering reviews and deploy real-time digital drone surveillance on lagging packages.",
            action_type="INTERIM_MITIGATION",
            description="Accelerate monitoring cadence to weekly engineering reviews with aerial drone progress validation.",
            rationale=f"Addresses early risk signals on {top_id or 'critical path'} by tightening reporting latency.",
            hypothesis_ids=[top_id] if top_id else [],
            evidence_ids=primary_ev_ids[:1],
            expected_benefit=0.68,
            expected_cost=0.22,
            expected_risk_reduction=0.60,
            implementation_risk=0.12,
            authority_score=0.82,
            responsible_stakeholder="Project Management Consultant (PMC) & Superintending Engineer",
            urgency="MEDIUM",
            approval_class="routine",
            tradeoffs="Adds reporting burden on contractor site staff without increasing physical throughput.",
            risks="Contractor administrative fatigue.",
            uncertainty="LOW",
            expected_impact="Eliminates reporting lag and provides early detection of new physical stalls",
            generated_by="hypothesis_action"
        ))

        # B. Technical Forensic Site Inspection
        candidates.append(RecommendationCandidate(
            id=f"REC-HYP-{len(candidates)+1:02d}",
            title="Deploy Joint Fact-Finding Technical Inspection to collect targeted on-site measurements and resolve open evidence gaps.",
            action_type="FORENSIC_AUDIT",
            description="Multi-disciplinary engineering inspection team dispatched to ground zero.",
            rationale="Resolves diagnostic ambiguity and tests ground truth against reported documentation.",
            hypothesis_ids=[top_id] if top_id else [],
            evidence_ids=primary_ev_ids[:2],
            expected_benefit=0.74,
            expected_cost=0.28,
            expected_risk_reduction=0.70,
            implementation_risk=0.15,
            authority_score=0.88,
            responsible_stakeholder="Superintending Engineer & PMU Technical Auditor",
            urgency="MEDIUM",
            approval_class="managerial",
            tradeoffs="Defers major contract interventions by 15-20 days pending physical site audit.",
            risks="Slight administrative delay in executing punitive contractual measures.",
            uncertainty="MEDIUM",
            expected_impact="Eliminates diagnostic ambiguity and prevents premature or wrongful contractual penalties",
            generated_by="hypothesis_action"
        ))

        # --------------------------------------------------------------------
        # Source 4: Evidence-Driven Actions (Data Quality & Peer Alignment)
        # --------------------------------------------------------------------
        # Stale data / contradiction refresh candidate
        if getattr(investigation_state, "contradictions", []) or "history" in str(getattr(investigation_state, "evidence_gaps", [])):
            candidates.append(RecommendationCandidate(
                id=f"REC-EVI-{len(candidates)+1:02d}",
                title="Issue formal data reconciliation notice to executing agency to resolve conflicting progress and milestone reports.",
                action_type="DATA_REFRESH",
                description="Mandates immediate statutory data reconciliation between field log and central PMIS.",
                rationale="Material contradictions detected between official progress records and milestone schedules.",
                hypothesis_ids=[],
                evidence_ids=[eid for eid in state_ev_ids if "contradiction" in eid] or primary_ev_ids[:1],
                expected_benefit=0.62,
                expected_cost=0.12,
                expected_risk_reduction=0.55,
                implementation_risk=0.08,
                authority_score=0.85,
                responsible_stakeholder="Chief Project Monitoring Officer",
                urgency="HIGH",
                approval_class="managerial",
                tradeoffs="Does not resolve physical bottlenecks; focuses on data integrity.",
                risks="Contractor delays submitting certified accounts.",
                uncertainty="LOW",
                expected_impact="Resolves conflicting telemetry and establishes unified project ground truth",
                generated_by="evidence_rule"
            ))

        # --------------------------------------------------------------------
        # Source 5: Standard Baseline Fallback
        # --------------------------------------------------------------------
        candidates.append(RecommendationCandidate(
            id=f"REC-BAS-{len(candidates)+1:02d}",
            title="Conduct comprehensive inter-ministerial review to assess project risk drivers and establish revised monitoring baselines.",
            action_type="BASELINE_REVIEW",
            description="Routine inter-ministerial PMU review to establish baseline tracking.",
            rationale="Composite risk metrics elevated across multiple operational indicators.",
            hypothesis_ids=[],
            evidence_ids=primary_ev_ids[:1],
            expected_benefit=0.55,
            expected_cost=0.35,
            expected_risk_reduction=0.48,
            implementation_risk=0.18,
            authority_score=0.80,
            responsible_stakeholder="Project Monitoring Unit (PMU)",
            urgency="MEDIUM",
            approval_class="routine",
            tradeoffs="Requires multi-ministry convening and inter-departmental consensus, taking 30-45 days.",
            risks="Administrative inertia and delayed decisive on-site intervention.",
            uncertainty="HIGH",
            expected_impact="Identifies root-cause bottlenecks and resets monitoring trajectory",
            generated_by="playbook"
        ))

        return candidates
