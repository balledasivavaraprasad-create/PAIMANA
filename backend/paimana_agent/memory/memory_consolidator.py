"""Precedent Consolidation and Lifecycle Management Engine.

Promotes completed investigations into candidate precedents and consolidates
empirical outcomes into fully validated institutional precedents.
"""
from __future__ import annotations
import time
from typing import Optional, Any
from .models import (
    Precedent, PrecedentContext, PrecedentProvenance, PrecedentStatus,
    AttributionClass, InvestigationMemory
)
from .pattern_fingerprint import PatternFingerprintBuilder
from .outcome_evaluator import OutcomeEvaluator
from .memory_reliability import MemoryReliabilityManager
from .precedent_memory import PrecedentMemoryStore


class MemoryConsolidator:
    """Manages the lifecycle transition from investigation state to validated precedent."""

    def __init__(self, store: PrecedentMemoryStore):
        self.store = store

    def create_candidate_from_investigation(self, state: Any,
                                            recommendation: Optional[dict] = None) -> Optional[Precedent]:
        """Extracts a CANDIDATE precedent from a completed InvestigationState.

        Candidate status marks it as unproven until real-world outcome is recorded.
        """
        # Require minimum confidence before creating a candidate
        conf_val = getattr(state, "confidence_score", None)
        if conf_val is None or conf_val == 0.0:
            raw_conf = getattr(state, "confidence", 0.0)
            if isinstance(raw_conf, str):
                conf_val = 0.85 if raw_conf == "HIGH" else 0.55 if raw_conf == "MEDIUM" else 0.25
            else:
                conf_val = float(raw_conf or 0.0)
        rc_conf = float(getattr(state, "root_cause_confidence", 0.0) or 0.0)
        conf = max(float(conf_val or 0.0), rc_conf)
        if conf < 0.50:
            return None

        project = getattr(state, "project", {}) or {}
        p_code = project.get("project_code") or getattr(state, "project_code", "UNKNOWN")
        events = getattr(state, "events", None) or getattr(state, "triggering_events", []) or []
        facts = getattr(state, "facts", []) or []
        hypotheses = getattr(state, "hypotheses", []) or []

        # Find best supported hypothesis
        best_hyp = None
        max_score = -1.0
        for h in hypotheses:
            score = float(h.get("confidence", 0.0) if isinstance(h, dict) else getattr(h, "confidence", 0.0))
            status = str(h.get("status", "") if isinstance(h, dict) else getattr(h, "status", "")).upper()
            if score > max_score and status in {"CONFIRMED", "LIKELY", "ACTIVE", "SUPPORTED", "PRIMARY"}:
                max_score = score
                best_hyp = h

        if best_hyp:
            root_cause = str(best_hyp.get("statement", "") if isinstance(best_hyp, dict) else getattr(best_hyp, "statement", getattr(best_hyp, "name", "Unspecified root cause")))
        else:
            root_cause = "Unspecified root cause"

        rec_obj = recommendation or getattr(state, "selected_recommendation", None) or {}
        if hasattr(rec_obj, "to_dict"):
            rec = rec_obj.to_dict()
        elif isinstance(rec_obj, dict):
            rec = dict(rec_obj)
        else:
            rec = {
                "action": getattr(rec_obj, "action", getattr(rec_obj, "title", str(rec_obj))),
                "action_type": getattr(rec_obj, "action_type", "GENERAL_ACTION"),
                "expected_impact": getattr(rec_obj, "expected_impact", {}),
            }

        # Context extraction
        cost_val = float(project.get("original_cost_cr") or 0.0)
        cost_band = "Mega (>1000Cr)" if cost_val >= 1000 else "Standard (150-1000Cr)" if cost_val >= 150 else "Minor (<150Cr)"
        prog_val = float(project.get("physical_progress_pct") or 0.0)
        stage = "Early (<25%)" if prog_val < 25 else "Mid (25-75%)" if prog_val <= 75 else "Late (>75%)"

        ctx = PrecedentContext(
            sector=str(project.get("sector") or "General Infrastructure"),
            project_type=str(project.get("project_type") or "Infrastructure Project"),
            project_size_cr=cost_val,
            cost_band=cost_band,
            stage_bracket=stage,
            implementing_agency=str(project.get("agency") or project.get("implementing_agency") or ""),
            state=str(project.get("state") or ""),
            contract_type=str(project.get("contract_type") or "EPC"),
        )

        fingerprint = PatternFingerprintBuilder.build_fingerprint(
            p=project,
            feats=getattr(state, "observations", {}).get("features", {}),
            events=events
        )

        prec_id = f"PREC-CAND-{p_code}-{int(time.time())}"
        title = f"Candidate Precedent: {p_code} - {root_cause[:50]}"

        ev_pattern = []
        for f in facts[:5]:
            if isinstance(f, dict):
                ev_pattern.append(f.get("claim", str(f)))
            else:
                ev_pattern.append(getattr(f, "claim", getattr(f, "statement", str(f))))

        hyp_pattern = []
        for h in hypotheses[:3]:
            if isinstance(h, dict):
                hyp_pattern.append(str(h.get("id", str(h))))
            else:
                hyp_pattern.append(str(getattr(h, "id", getattr(h, "statement", str(h)))))

        ev_events = []
        for e in events:
            if isinstance(e, dict):
                ev_events.append(e.get("type", str(e)))
            else:
                ev_events.append(getattr(e, "type", str(e)))

        candidate = Precedent(
            id=prec_id,
            title=title,
            event_pattern={"events": ev_events},
            pattern_fingerprint=fingerprint,
            context=ctx,
            evidence_pattern=ev_pattern,
            hypothesis_pattern=hyp_pattern,
            root_cause=root_cause,
            root_cause_confidence=conf,
            intervention=rec,
            intervention_class=rec.get("action_type") or rec.get("template_id") or "GENERAL_ACTION",
            expected_outcome=rec.get("expected_impact") or {},
            source_investigation_id=str(getattr(state, "investigation_id", prec_id)),
            source_project_id=p_code,
            provenance=PrecedentProvenance(
                source_investigation_ids=[str(getattr(state, "investigation_id", prec_id))],
                source_project_codes=[p_code],
                independence_group_ids=[f"proj_{p_code}"]
            ),
            status="CANDIDATE",
            application_count=1,
            success_count=0,
            failure_count=0,
            memory_reliability=0.30,
            transferability_score=0.70
        )
        candidate.memory_reliability = MemoryReliabilityManager.compute_reliability(candidate)

        self.store.add_precedent(candidate)
        return candidate

    def evaluate_and_consolidate(self, precedent_id: str,
                                 pre_metrics: dict, post_metrics: dict,
                                 confounders: Optional[list[str]] = None,
                                 independence_group: Optional[str] = None) -> Precedent:
        """Evaluates observed empirical outcome and transitions CANDIDATE -> VALIDATED or FAILED."""
        precedent = self.store.get_precedent(precedent_id)
        if not precedent:
            raise ValueError(f"Precedent {precedent_id} not found.")

        eval_res = OutcomeEvaluator.evaluate_outcome(
            pre_metrics=pre_metrics,
            post_metrics=post_metrics,
            intervention_details=precedent.intervention,
            confounders_reported=confounders
        )

        precedent.observed_outcome = {
            "evaluation": eval_res,
            "recorded_at": time.time(),
            "pre_metrics": pre_metrics,
            "post_metrics": post_metrics,
        }
        precedent.attribution_class = eval_res["attribution_class"]
        precedent.outcome_quality = eval_res["outcome_quality"]
        precedent.intervention_effectiveness = eval_res["effectiveness_ratio"]
        precedent.last_validated_at = time.time()

        # Transition status based on empirical evaluation
        if eval_res["attribution_class"] in {"LIKELY_EFFECTIVE", "POSSIBLY_EFFECTIVE"}:
            precedent.status = "VALIDATED"
        elif eval_res["attribution_class"] in {"FAILED", "LIKELY_INEFFECTIVE"}:
            precedent.status = "VALIDATED"  # Stored as validated failure precedent
        else:
            precedent.status = "PROVISIONAL"

        # Update success/failure counters & reliability with new status
        is_success = eval_res["is_success"]
        MemoryReliabilityManager.record_application_outcome(
            precedent=precedent,
            success=is_success,
            independence_group=independence_group
        )

        self.store.add_precedent(precedent)
        return precedent
