"""Hybrid Precedent Retrieval Engine.

Performs multi-criteria precedent matching incorporating pattern fingerprint similarity,
contextual transferability, empirical reliability, and temporal decay.
Produces a balanced PrecedentBundle with supporting cases, failures, and counterexamples.
"""
from __future__ import annotations
from typing import Optional, Any
from .models import (
    Precedent, PrecedentBundle, PatternFingerprint, PrecedentContext
)
from .pattern_fingerprint import PatternMatcher, PatternFingerprintBuilder
from .transferability import TransferabilityEvaluator
from .memory_decay import MemoryDecayManager
from .failure_memory import FailureMemoryManager
from .precedent_memory import PrecedentMemoryStore


class MemoryRetriever:
    """Retrieves relevant institutional precedents for a target investigation."""

    def __init__(self, store: PrecedentMemoryStore):
        self.store = store

    def retrieve(self, target_project: dict,
                 target_pattern: Optional[PatternFingerprint] = None,
                 target_context: Optional[PrecedentContext] = None,
                 active_hypotheses: Optional[list[str]] = None,
                 limit: int = 5) -> PrecedentBundle:
        """Retrieves a balanced PrecedentBundle for the current project and pattern."""
        p_code = target_project.get("project_code", "UNKNOWN")

        # 1. Build Target Fingerprint & Context if not provided
        if target_pattern is None:
            target_pattern = PatternFingerprintBuilder.build_fingerprint(target_project)

        if target_context is None:
            cost_val = float(target_project.get("original_cost_cr") or 0.0)
            cost_band = "Mega (>1000Cr)" if cost_val >= 1000 else "Standard (150-1000Cr)" if cost_val >= 150 else "Minor (<150Cr)"
            prog_val = float(target_project.get("physical_progress_pct") or 0.0)
            stage = "Early (<25%)" if prog_val < 25 else "Mid (25-75%)" if prog_val <= 75 else "Late (>75%)"

            target_context = PrecedentContext(
                sector=str(target_project.get("sector") or "General Infrastructure"),
                project_type=str(target_project.get("project_type") or "Civil Infrastructure"),
                project_size_cr=cost_val,
                cost_band=cost_band,
                stage_bracket=stage,
                implementing_agency=str(target_project.get("agency") or target_project.get("implementing_agency") or ""),
                contract_type=str(target_project.get("contract_type") or "EPC"),
            )

        # 2. Score Candidates
        all_candidates = self.store.list_all()
        scored_candidates = []

        for p in all_candidates:
            if p.status in {"REJECTED", "CONTRADICTED"}:
                continue

            pat_sim = PatternMatcher.similarity(target_pattern, p.pattern_fingerprint)
            trans_score = TransferabilityEvaluator.evaluate(p.context, target_context)
            rel_score = p.memory_reliability
            decay_factor = MemoryDecayManager.calculate_decay(p.created_at)

            # Strong discounting if transferability is fundamentally poor
            trans_multiplier = 1.0 if trans_score >= 0.40 else 0.50

            composite = (
                0.40 * pat_sim +
                0.35 * trans_score +
                0.15 * rel_score +
                0.10 * decay_factor
            ) * trans_multiplier

            # Store the computed transferability directly on the candidate instance for downstream consumption
            p.transferability_score = trans_score

            scored_candidates.append({
                "precedent": p,
                "composite_score": round(composite, 3),
                "pattern_similarity": pat_sim,
                "transferability": trans_score,
                "reliability": rel_score,
                "decay": decay_factor,
            })

        # Sort by composite score descending
        scored_candidates.sort(key=lambda x: x["composite_score"], reverse=True)

        supporting: list[Precedent] = []
        failed: list[Precedent] = []
        counterexamples: list[Precedent] = []
        relevance_exps: list[dict] = []
        rec_hypotheses: set[str] = set()
        rec_tools: set[str] = set()
        guidance_notes: list[str] = []

        # 3. Segregate into Supporting, Failed, and Counterexamples
        for item in scored_candidates:
            p = item["precedent"]
            comp = item["composite_score"]

            if p.is_counterexample:
                if len(counterexamples) < 3:
                    counterexamples.append(p)
                    relevance_exps.append({
                        "id": p.id,
                        "type": "COUNTEREXAMPLE",
                        "score": comp,
                        "explanation": f"Counterexample for {p.counterexample_for_hypotheses}: {p.why_relevant}"
                    })
                continue

            if FailureMemoryManager.index_failure(p):
                if len(failed) < 3:
                    failed.append(p)
                    relevance_exps.append({
                        "id": p.id,
                        "type": "FAILURE_WARNING",
                        "score": comp,
                        "explanation": f"Warning: Past failure in {p.source_project_id or p.id}. {p.why_relevant or p.usage_guidance}"
                    })
                    if p.usage_guidance:
                        guidance_notes.append(f"Aversion Warning: {p.usage_guidance}")
                continue

            # Standard / Supporting precedent
            if comp >= 0.45 and len(supporting) < limit:
                supporting.append(p)
                relevance_exps.append({
                    "id": p.id,
                    "type": "SUPPORTING",
                    "score": comp,
                    "pattern_similarity": item["pattern_similarity"],
                    "transferability": item["transferability"],
                    "explanation": f"Similar pattern in {p.source_project_id or p.id} ({p.title}). Root cause: {p.root_cause}"
                })
                for h in p.hypothesis_pattern:
                    rec_hypotheses.add(h)
                if p.usage_guidance:
                    guidance_notes.append(f"Precedent Advice: {p.usage_guidance}")

        # Also search for explicit counterexamples if hypotheses are provided
        if active_hypotheses:
            for h in active_hypotheses:
                cex_list = self.store.find_counterexamples(target_pattern, hypothesis=h)
                for cex in cex_list:
                    if cex not in counterexamples and len(counterexamples) < 3:
                        counterexamples.append(cex)
                        relevance_exps.append({
                            "id": cex.id,
                            "type": "COUNTEREXAMPLE",
                            "score": 0.80,
                            "explanation": f"Explicit counterexample for '{h}': {cex.why_relevant}"
                        })

        return PrecedentBundle(
            target_project_code=p_code,
            target_pattern=target_pattern,
            supporting_precedents=supporting,
            failed_precedents=failed,
            counterexamples=counterexamples,
            relevance_explanations=relevance_exps,
            recommended_hypotheses=sorted(list(rec_hypotheses)),
            recommended_tools=sorted(list(rec_tools)),
            recommendation_guidance=guidance_notes
        )
