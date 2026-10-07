"""Evidence Gap Analyzer for Dynamic Uncertainty Detection.

Analyzes the current investigation state (known evidence, unexplained findings,
competing hypotheses, contradictions) and generates prioritized EvidenceNeed objects.
"""
from __future__ import annotations
from typing import Any, Optional
from .evidence_need import EvidenceNeed


class EvidenceGapAnalyzer:
    """Detects active information gaps and translates them into first-class EvidenceNeeds."""

    def analyze_needs(self, state: Any, p: dict, feats: dict,
                      event_types: list[str]) -> list[EvidenceNeed]:
        """Analyzes state and produces prioritized list of open and tracked EvidenceNeeds."""
        existing_needs = {n.id: n for n in getattr(state, "evidence_needs", [])}
        used_tools = set(getattr(state, "tools_used", []))
        obs = getattr(state, "observations", {})

        # --------------------------------------------------------------------
        # 1. Financial Velocity Need
        # --------------------------------------------------------------------
        need_fin_id = "need_financial_velocity"
        spend_gap = float(feats.get("progress_expenditure_gap_pct", 0.0))
        is_mismatch = "COST_PROGRESS_MISMATCH" in event_types or spend_gap > 15.0
        prio_fin = 0.95 if is_mismatch else (0.75 if "milestone_audit" in used_tools else 0.40)
        urg_fin = 0.95 if is_mismatch else (0.70 if "milestone_audit" in used_tools else 0.35)

        if need_fin_id not in existing_needs:
            existing_needs[need_fin_id] = EvidenceNeed(
                id=need_fin_id,
                question="Verify physical progress vs cumulative expenditure velocity to audit potential disbursement decoupling.",
                target_hypothesis_ids=["front_loaded_billing", "underreported_cost_escalation", "reporting_discrepancy"],
                required_evidence_types=["financial_audit", "burn_rate", "disbursement_velocity"],
                priority=prio_fin,
                discrimination_power=0.90,
                urgency=urg_fin,
                freshness_requirement=0.80,
                status="OPEN"
            )
        else:
            existing_needs[need_fin_id].priority = prio_fin
            existing_needs[need_fin_id].urgency = urg_fin

        if "financial_velocity" in used_tools and existing_needs[need_fin_id].status == "OPEN":
            existing_needs[need_fin_id].mark_satisfied("financial_velocity")

        # --------------------------------------------------------------------
        # 2. Milestone Audit Need
        # --------------------------------------------------------------------
        need_mile_id = "need_milestone_audit"
        slip_months = float(feats.get("completion_delay_months", 0.0))
        is_delay = "MILESTONE_DELAYED" in event_types or "PROGRESS_STALLED" in event_types or slip_months > 0
        prio_mile = 0.95 if is_delay else (0.80 if "financial_velocity" in used_tools else 0.40)
        urg_mile = 0.95 if is_delay else (0.70 if "financial_velocity" in used_tools else 0.35)

        if need_mile_id not in existing_needs:
            existing_needs[need_mile_id] = EvidenceNeed(
                id=need_mile_id,
                question="Audit milestone completion schedule, target slippage, and lifespan ratios.",
                target_hypothesis_ids=["chronic_schedule_delay", "unrealistic_original_dpr_timeline", "land_acquisition_stalling"],
                required_evidence_types=["schedule_milestone", "timeline_slippage", "duration_ratio"],
                priority=prio_mile,
                discrimination_power=0.88,
                urgency=urg_mile,
                freshness_requirement=0.80,
                status="OPEN"
            )
        else:
            existing_needs[need_mile_id].priority = prio_mile
            existing_needs[need_mile_id].urgency = urg_mile

        if "milestone_audit" in used_tools and existing_needs[need_mile_id].status == "OPEN":
            existing_needs[need_mile_id].mark_satisfied("milestone_audit")

        # --------------------------------------------------------------------
        # 3. Disambiguate Contradictions via Project Trajectory
        # --------------------------------------------------------------------
        need_hist_id = "need_project_history"
        has_contra = bool(getattr(state, "contradictions", []))
        is_accel = "RISK_ACCELERATING" in event_types
        if need_hist_id not in existing_needs:
            prio = 0.92 if is_accel else (0.88 if has_contra else 0.50)
            existing_needs[need_hist_id] = EvidenceNeed(
                id=need_hist_id,
                question="Audit multi-month risk score trajectory and issue log to disambiguate progress contradictions or score jumps.",
                target_hypothesis_ids=["reporting_discrepancy", "chronic_schedule_delay", "underreported_cost_escalation"],
                required_evidence_types=["trajectory_history", "risk_jump", "issue_log"],
                priority=prio,
                discrimination_power=0.85,
                urgency=0.85 if (has_contra or is_accel) else 0.40,
                freshness_requirement=0.60,
                status="OPEN"
            )
        elif has_contra and existing_needs[need_hist_id].status == "OPEN":
            # Boost priority if new contradiction surfaced
            existing_needs[need_hist_id].priority = max(existing_needs[need_hist_id].priority, 0.90)
            existing_needs[need_hist_id].urgency = max(existing_needs[need_hist_id].urgency, 0.85)

        if "project_history" in used_tools and existing_needs[need_hist_id].status == "OPEN":
            existing_needs[need_hist_id].mark_satisfied("project_history")

        # --------------------------------------------------------------------
        # 4. Contextual Peer Benchmarking Need
        # --------------------------------------------------------------------
        need_peer_id = "need_peer_intelligence"
        if need_peer_id not in existing_needs:
            # High priority after initial physical or financial audit
            prio = 0.78 if ("financial_velocity" in used_tools or "milestone_audit" in used_tools) else 0.55
            existing_needs[need_peer_id] = EvidenceNeed(
                id=need_peer_id,
                question="Benchmark metrics against comparable sector peers and national baselines to test for systemic vs project-specific bottlenecks.",
                target_hypothesis_ids=["unrealistic_original_dpr_timeline", "chronic_schedule_delay", "land_acquisition_stalling"],
                required_evidence_types=["peer_baseline", "cohort_benchmark", "national_stats"],
                priority=prio,
                discrimination_power=0.80,
                urgency=0.65,
                freshness_requirement=0.50,
                status="OPEN"
            )
        if "peer_intelligence" in used_tools and existing_needs[need_peer_id].status == "OPEN":
            existing_needs[need_peer_id].mark_satisfied("peer_intelligence")

        # --------------------------------------------------------------------
        # 5. Precedent Learning & Intervention Outcome Retrieval
        # --------------------------------------------------------------------
        need_mem_id = "need_memory_retrieval"
        hypotheses = getattr(state, "hypotheses", [])
        top_conf = max([getattr(h, "confidence_score", 0.0) if hasattr(h, "confidence_score") else 0.0 for h in hypotheses], default=0.0)
        if need_mem_id not in existing_needs:
            prio = 0.82 if (top_conf >= 0.40 or len(used_tools) >= 2) else 0.50
            existing_needs[need_mem_id] = EvidenceNeed(
                id=need_mem_id,
                question="Retrieve past intervention outcomes and empirical precedents to calibrate confidence and recommend vetted actions.",
                target_hypothesis_ids=["chronic_schedule_delay", "front_loaded_billing", "underreported_cost_escalation"],
                required_evidence_types=["precedent_memory", "intervention_outcome", "learning_calibration"],
                priority=prio,
                discrimination_power=0.75,
                urgency=0.70 if len(used_tools) >= 2 else 0.40,
                freshness_requirement=0.40,
                status="OPEN"
            )
        if "memory_retrieval" in used_tools and existing_needs[need_mem_id].status == "OPEN":
            existing_needs[need_mem_id].mark_satisfied("memory_retrieval")

        # --------------------------------------------------------------------
        # 6. Model Explainability / Attribution Need
        # --------------------------------------------------------------------
        need_shap_id = "need_shap_attribution"
        if need_shap_id not in existing_needs:
            existing_needs[need_shap_id] = EvidenceNeed(
                id=need_shap_id,
                question="Quantify SHAP feature permutation attributions for ML model risk drivers.",
                target_hypothesis_ids=["underreported_cost_escalation", "chronic_schedule_delay", "front_loaded_billing"],
                required_evidence_types=["model_attribution", "shap_values", "risk_drivers"],
                priority=0.55 if len(used_tools) >= 3 else 0.40,
                discrimination_power=0.70,
                urgency=0.40,
                freshness_requirement=0.70,
                status="OPEN"
            )
        if "shap_attribution" in used_tools and existing_needs[need_shap_id].status == "OPEN":
            existing_needs[need_shap_id].mark_satisfied("shap_attribution")

        # --------------------------------------------------------------------
        # 7. Dynamic Competing Hypotheses Discrimination Need
        # --------------------------------------------------------------------
        active_hypos = [h for h in hypotheses if getattr(h, "status", "").lower() in ["active", "supported", "primary", "candidate"]]
        if len(active_hypos) >= 2:
            h1, h2 = active_hypos[0], active_hypos[1]
            c1 = getattr(h1, "confidence_score", getattr(h1, "confidence", 0.5))
            c2 = getattr(h2, "confidence_score", getattr(h2, "confidence", 0.5))
            if isinstance(c1, str):
                c1 = 0.85 if c1 == "HIGH" else (0.50 if c1 == "MEDIUM" else 0.20)
            if isinstance(c2, str):
                c2 = 0.85 if c2 == "HIGH" else (0.50 if c2 == "MEDIUM" else 0.20)
            
            # If top two hypotheses are closely contested (margin < 0.20)
            if abs(c1 - c2) < 0.20:
                disc_id = f"need_discriminate_{getattr(h1, 'id', 'h1')}_{getattr(h2, 'id', 'h2')}"
                if disc_id not in existing_needs:
                    # Target evidence type aligns with trigger context
                    if "COST_PROGRESS_MISMATCH" in event_types or is_mismatch:
                        req_types = ["financial_audit", "burn_rate"]
                    elif "MILESTONE_DELAYED" in event_types or is_delay:
                        req_types = ["schedule_milestone", "timeline_slippage"]
                    else:
                        req_types = ["schedule_milestone", "peer_baseline", "financial_audit"]

                    existing_needs[disc_id] = EvidenceNeed(
                        id=disc_id,
                        question=f"Discriminate between competing root causes: '{getattr(h1, 'statement', h1)}' vs '{getattr(h2, 'statement', h2)}'.",
                        target_hypothesis_ids=[getattr(h1, "id", "h1"), getattr(h2, "id", "h2")],
                        required_evidence_types=req_types,
                        priority=0.92,
                        discrimination_power=0.95,
                        urgency=0.90,
                        freshness_requirement=0.75,
                        status="OPEN"
                    )

        # --------------------------------------------------------------------
        # 8. Unverified Causal Mechanism Transmission Gaps
        # --------------------------------------------------------------------
        if len(used_tools) > 0:
            causal_claims = getattr(state, "causal_claims", [])
            for claim_dict in causal_claims:
                if claim_dict.get("status") in ["REJECTED", "UNRESOLVED"]:
                    continue
                mech_dict = claim_dict.get("mechanism")
                if not mech_dict:
                    continue
                links = mech_dict.get("links_verified", {})
                unverified_vars = [var for var, ok in links.items() if not ok]
                if unverified_vars:
                    c_id = claim_dict.get("hypothesis_id") or claim_dict.get("id") or "cause"
                    need_mech_id = f"need_mech_transmission_{c_id}"
                    if need_mech_id not in existing_needs:
                        req_types = []
                        for v in unverified_vars:
                            if any(w in v for w in ["bill", "disbursement", "advance", "payment", "escrow", "cashflow"]):
                                req_types.extend(["financial_audit", "disbursement_velocity", "burn_rate"])
                            elif any(w in v for w in ["equipment", "manpower", "machinery", "productivity", "mobilization"]):
                                req_types.extend(["schedule_milestone", "timeline_slippage"])
                            elif any(w in v for w in ["clearance", "approval", "turnaround", "row", "possession"]):
                                req_types.extend(["regulatory_clearance", "schedule_milestone"])
                            elif any(w in v for w in ["portal", "entry", "reconciliation", "mpr"]):
                                req_types.extend(["trajectory_history", "schedule_milestone"])
                        if not req_types:
                            req_types = ["financial_audit", "schedule_milestone"]

                        existing_needs[need_mech_id] = EvidenceNeed(
                            id=need_mech_id,
                            question=f"Verify unconfirmed intermediate causal links for '{claim_dict.get('proposed_cause')}': {', '.join(unverified_vars[:3])}.",
                            target_hypothesis_ids=[c_id],
                            required_evidence_types=list(dict.fromkeys(req_types)),
                            priority=0.88,
                            discrimination_power=0.90,
                            urgency=0.85,
                            freshness_requirement=0.75,
                            status="OPEN"
                        )

        # --------------------------------------------------------------------
        # 9. Unresolved Confounder Elimination Gaps
        # --------------------------------------------------------------------
        confounders = getattr(state, "confounders", [])
        for conf in confounders:
            var_name = conf.get("variable", "") if isinstance(conf, dict) else getattr(conf, "variable", "")
            is_resolved = conf.get("resolved", False) if isinstance(conf, dict) else getattr(conf, "resolved", False)
            if var_name and not is_resolved:
                need_conf_id = f"need_confounder_{var_name.lower().replace(' ', '_')}"
                if need_conf_id not in existing_needs:
                    existing_needs[need_conf_id] = EvidenceNeed(
                        id=need_conf_id,
                        question=f"Disambiguate common cause / potential confounder: '{var_name}' across competing explanations.",
                        target_hypothesis_ids=[getattr(h, "id", str(h)) for h in hypotheses],
                        required_evidence_types=["peer_baseline", "trajectory_history", "cohort_benchmark"],
                        priority=0.85,
                        discrimination_power=0.88,
                        urgency=0.80,
                        freshness_requirement=0.60,
                        status="OPEN"
                    )

        # --------------------------------------------------------------------
        # 10. Unexplained Evidence Resolution Gaps
        # --------------------------------------------------------------------
        unexplained = getattr(state, "unexplained_evidence", [])
        if unexplained:
            need_unexp_id = "need_unexplained_evidence_resolution"
            if need_unexp_id not in existing_needs:
                sample_claims = [getattr(e, "claim", str(e)) for e in unexplained[:2]]
                existing_needs[need_unexp_id] = EvidenceNeed(
                    id=need_unexp_id,
                    question=f"Gather discriminating evidence to explain unaccounted findings: {'; '.join(sample_claims)}.",
                    target_hypothesis_ids=[getattr(h, "id", str(h)) for h in hypotheses],
                    required_evidence_types=["trajectory_history", "peer_baseline", "model_attribution"],
                    priority=0.82,
                    discrimination_power=0.85,
                    urgency=0.75,
                    freshness_requirement=0.70,
                    status="OPEN"
                )

        return list(existing_needs.values())
