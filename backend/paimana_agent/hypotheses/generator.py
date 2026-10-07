"""Hypothesis Generator for proposing novel causal explanations during investigations.

Employs deterministic trigger conditions (unexplained material evidence, weak active hypotheses,
cross-source contradictions) to invoke LLM-driven generation with a structured JSON contract
and intelligent deterministic fallback.
"""
from __future__ import annotations
import json
import logging
import urllib.request
from typing import Any, Optional
from .model import Hypothesis

logger = logging.getLogger("paimana_agent.hypotheses.generator")


class HypothesisGenerator:
    """Generates novel hypothesis candidates when existing hypotheses fail to explain observations."""

    def __init__(self, llm_cfg: Optional[dict] = None):
        self.cfg = llm_cfg or {}
        self.enabled = bool(self.cfg.get("enabled", False))
        self.url = self.cfg.get("url", "http://localhost:11434/api/generate")
        self.model = self.cfg.get("model", "llama3.1:8b")
        self.timeout = float(self.cfg.get("timeout", 15))
        self._gen_counter = 0

    def should_generate(
        self,
        unexplained_evidence: list[Any],
        active_hypotheses: list[Hypothesis],
        has_contradictions: bool,
        iteration: int,
        converged: bool = False
    ) -> tuple[bool, str]:
        """Evaluates deterministic trigger conditions A, B, C, D, E."""
        # Condition A: Material evidence is unexplained
        if unexplained_evidence:
            return True, f"Condition A: {len(unexplained_evidence)} material evidence item(s) unexplained by active hypotheses."

        # Condition B: All active hypotheses are weak
        if active_hypotheses:
            best_conf = max(h.confidence for h in active_hypotheses)
            if best_conf < 0.35:
                return True, f"Condition B: All active hypotheses are weak (highest confidence is {best_conf:.2f} < 0.35)."

        # Condition C: Strong contradiction exists and active hypotheses are contradicted
        if has_contradictions and all(h.status in ["weakened", "rejected"] for h in active_hypotheses):
            return True, "Condition C: Strong data contradictions exist and all active hypotheses are weakened or rejected."

        # Condition D: Multi-step investigation without convergence
        if iteration >= 3 and not converged:
            top_margin = 0.0
            if len(active_hypotheses) >= 2:
                top_margin = abs(active_hypotheses[0].confidence - active_hypotheses[1].confidence)
            if top_margin < 0.10:
                return True, f"Condition D: Investigation at iteration {iteration} lacks convergence (margin {top_margin:.2f})."

        return False, "Hypothesis generation not triggered."

    def generate_candidates(
        self,
        unexplained_evidence: list[Any],
        active_hypotheses: list[Hypothesis],
        project_context: dict,
        iteration: int,
        max_candidates: int = 2
    ) -> list[Hypothesis]:
        """Generates novel candidate hypotheses matching the strict generation contract."""
        candidates: list[Hypothesis] = []

        # 1. Attempt LLM generation if enabled
        if self.enabled:
            candidates = self._generate_with_llm(unexplained_evidence, active_hypotheses, project_context, iteration, max_candidates)

        # 2. Fallback to deterministic domain hypothesis synthesis if LLM returned nothing
        if not candidates:
            candidates = self._generate_deterministic_fallback(unexplained_evidence, active_hypotheses, project_context, iteration, max_candidates)

        return candidates[:max_candidates]

    def _generate_with_llm(
        self,
        unexplained: list[Any],
        active_hypo: list[Hypothesis],
        p: dict,
        iteration: int,
        max_candidates: int
    ) -> list[Hypothesis]:
        """Queries LLM with structured evidence context and parses JSON contract."""
        prompt_data = {
            "project_code": p.get("project_code"),
            "sector": p.get("sector"),
            "unexplained_evidence": [{"id": e.id, "claim": e.claim, "source": e.source_tool} for e in unexplained],
            "existing_hypotheses": [h.statement for h in active_hypo],
            "max_candidates": max_candidates,
        }
        prompt = (
            "You are the Senior Infrastructure Forensic Investigator for MoSPI projects.\n"
            "The following material evidence is NOT explained by any existing hypotheses.\n"
            "Formulate NEW causal hypothesis candidates that specifically explain this evidence.\n"
            "STRICT RULES:\n"
            "1. No invented numbers or unverified facts.\n"
            "2. Must be testable and falsifiable with observable predictions.\n"
            "3. Must specify discriminating evidence.\n"
            "Return JSON format:\n"
            "{\n"
            "  \"candidate_hypotheses\": [\n"
            "    {\n"
            "      \"statement\": \"...\",\n"
            "      \"mechanism\": \"...\",\n"
            "      \"predicted_observations\": [\"...\"],\n"
            "      \"supporting_evidence_ids\": [\"...\"],\n"
            "      \"contradicting_evidence_ids\": [],\n"
            "      \"discriminating_evidence\": [\"...\"],\n"
            "      \"confidence\": 0.40\n"
            "    }\n"
            "  ]\n"
            "}\n"
            f"Context: {json.dumps(prompt_data)}"
        )
        try:
            req_data = json.dumps({
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }).encode("utf-8")
            req = urllib.request.Request(self.url, data=req_data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                content = json.loads(raw.get("response", "{}"))
                cand_list = content.get("candidate_hypotheses", [])
                results = []
                for item in cand_list:
                    self._gen_counter += 1
                    h = Hypothesis(
                        id=f"H_gen_{self._gen_counter}",
                        statement=item.get("statement", ""),
                        source="agent_generated",
                        status="candidate",
                        mechanism=item.get("mechanism", ""),
                        predicted_observations=item.get("predicted_observations", []),
                        support_evidence_ids=item.get("supporting_evidence_ids", [e.id for e in unexplained]),
                        contradiction_evidence_ids=item.get("contradicting_evidence_ids", []),
                        discriminating_evidence=item.get("discriminating_evidence", []),
                        confidence=float(item.get("confidence", 0.40)),
                        created_at_iteration=iteration,
                        last_updated_iteration=iteration,
                        falsification_condition=f"Field audit or project records refute predicted observations: {', '.join(item.get('predicted_observations', []))}"
                    )
                    results.append(h)
                if results:
                    return results
        except Exception as ex:
            logger.debug(f"LLM hypothesis generation failed ({ex}); utilizing deterministic synthesis.")
        return []

    def _generate_deterministic_fallback(
        self,
        unexplained: list[Any],
        active_hypo: list[Hypothesis],
        p: dict,
        iteration: int,
        max_candidates: int
    ) -> list[Hypothesis]:
        """Deterministic domain synthesis to produce valid falsifiable candidates."""
        candidates = []
        unexplained_ids = [e.id for e in unexplained]
        claims_text = " ".join(e.claim.lower() for e in unexplained)

        # Pattern 1: Procurement / Tendering Bottleneck
        if any(term in claims_text for term in ["procurement", "tender", "contract", "retender", "dispute", "vendor"]):
            self._gen_counter += 1
            candidates.append(Hypothesis(
                id=f"H_gen_procurement_{self._gen_counter}",
                statement="Procurement & Tendering Impasse: Critical package retendering or contractor contract dispute has halted physical progress.",
                source="agent_generated",
                status="candidate",
                mechanism="Contract cancellation or protracted bid retendering creates administrative stall prior to re-mobilization.",
                predicted_observations=["tenders cancelled or retendered", "fresh bidding notice issued", "contractor mobilization paused"],
                support_evidence_ids=unexplained_ids,
                discriminating_evidence=["procurement milestone history", "bid evaluation committee records"],
                confidence=0.45,
                created_at_iteration=iteration,
                last_updated_iteration=iteration,
                falsification_condition="Executing agency procurement ledger confirms all project packages are formally awarded with active contractors on site."
            ))

        # Pattern 2: Environmental / Statutory Forest Clearance Stalling
        elif any(term in claims_text for term in ["forest", "environment", "clearance", "wildlife", "statutory", "approval", "row", "land"]):
            self._gen_counter += 1
            candidates.append(Hypothesis(
                id=f"H_gen_clearance_{self._gen_counter}",
                statement="Statutory Environmental & Land Handover Impasse: Environmental Stage-2 clearance or disputed RoW encumbrance halts construction.",
                source="agent_generated",
                status="candidate",
                mechanism="Lack of statutory tree-felling or forest land alienation permits prevents civil excavation.",
                predicted_observations=["stage-2 forest clearance pending", "untransferred RoW patches", "local administration objection"],
                support_evidence_ids=unexplained_ids,
                discriminating_evidence=["MoEFCC approval portal records", "district collector land handover certificate"],
                confidence=0.45,
                created_at_iteration=iteration,
                last_updated_iteration=iteration,
                falsification_condition="Parivesh environmental portal confirms Stage-2 forest/environmental clearances unconditionally granted."
            ))

        # Pattern 3: Contractor Cash-Flow / Liquidity Distress
        elif any(term in claims_text for term in ["stalled", "burn-down", "bank", "guarantee", "insolvency", "liquidity"]):
            self._gen_counter += 1
            candidates.append(Hypothesis(
                id=f"H_gen_liquidity_{self._gen_counter}",
                statement="Contractor Cash-Flow Distress: Lead contractor financial distress or working capital freeze prevents on-site procurement.",
                source="agent_generated",
                status="candidate",
                mechanism="Contractor unable to sustain credit lines for raw material deliveries (steel/cement) despite sanctioned project outlay.",
                predicted_observations=["subcontractor payment defaults", "delayed material procurement invoices", "reduced site manpower deployment"],
                support_evidence_ids=unexplained_ids,
                discriminating_evidence=["contractor running bills ledger", "site labor muster rolls"],
                confidence=0.40,
                created_at_iteration=iteration,
                last_updated_iteration=iteration,
                falsification_condition="Joint bank guarantee and contractor audited financial statement proves positive operational cash flow on project account."
            ))

        # Generic novel explanation when unexplained evidence exists without specific keyword
        if not candidates and unexplained:
            self._gen_counter += 1
            first_ev = unexplained[0]
            candidates.append(Hypothesis(
                id=f"H_gen_novel_{self._gen_counter}",
                statement=f"Specialized Site Deterioration Factor: Observed anomaly '{first_ev.claim[:80]}' represents an unclassified bottleneck.",
                source="agent_generated",
                status="candidate",
                mechanism=f"Independent operational bottleneck directly linked to evidence {first_ev.id}.",
                predicted_observations=[f"anomalous metric persists in {first_ev.source_tool}"],
                support_evidence_ids=[first_ev.id],
                discriminating_evidence=[f"{first_ev.source_tool} historical audit trail", "detailed project engineer log"],
                confidence=0.35,
                created_at_iteration=iteration,
                last_updated_iteration=iteration,
                falsification_condition=f"Subsequent audit of {first_ev.source_tool} proves the observed anomaly was a transient data lag rather than physical bottleneck."
            ))

        return candidates[:max_candidates]
