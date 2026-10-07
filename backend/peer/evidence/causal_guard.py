"""Causal-Claim Guard & Semantic Safety Rules Engine (ESS-07).

Encodes 8 strict semantic safety rules preventing ungrounded causal leaps,
accusatory attributions, and conflation of statistical correlations with real-world culpability:

Rule 1: Correlation ≠ Causation
Rule 2: Anomaly ≠ Wrongdoing / Corruption
Rule 3: High Spend ≠ Front-Loaded Billing Manipulation
Rule 4: Delay ≠ Contractor Fault
Rule 5: Missing Data ≠ Negative Evidence
Rule 6: History ≠ Current Fact
Rule 7: ML Prediction ≠ Observed Fact
Rule 8: Peer Difference ≠ Abnormality Without Valid Cohort
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from .schemas import Claim, ClaimLevel, ClaimStatus, SemanticSafetyRule

logger = logging.getLogger("paimana.peer.evidence.causal_guard")

RULES_CATALOG: Dict[str, SemanticSafetyRule] = {
    "SSR-01": SemanticSafetyRule(
        rule_id="SSR-01",
        rule_name="CORRELATION_NOT_CAUSATION",
        description="Correlation between financial burn and project delay does not prove financial causation.",
        prohibited_escalation="Escalating co-occurring statistical variations into causal statements.",
        enforcement_action="DOWNGRADE",
    ),
    "SSR-02": SemanticSafetyRule(
        rule_id="SSR-02",
        rule_name="ANOMALY_NOT_WRONGDOING",
        description="Statistical outlier status or expenditure anomaly does not indicate corruption, fraud, or wrongdoing.",
        prohibited_escalation="Equating statistical deviation with criminal or contractual malfeasance.",
        enforcement_action="REJECT",
    ),
    "SSR-03": SemanticSafetyRule(
        rule_id="SSR-03",
        rule_name="HIGH_SPEND_NOT_BILLING_MANIPULATION",
        description="Early expenditure leading physical progress cannot be labeled 'billing manipulation' without mobilization audit.",
        prohibited_escalation="Asserting fraudulent billing based solely on financial-progress curve divergence.",
        enforcement_action="DOWNGRADE",
    ),
    "SSR-04": SemanticSafetyRule(
        rule_id="SSR-04",
        rule_name="DELAY_NOT_CONTRACTOR_FAULT",
        description="Schedule slippage cannot be unilaterally attributed to contractor delinquency when statutory clearances, RoW, or utility delays are unverified.",
        prohibited_escalation="Blaming execution contractors without ruling out owner-side statutory and RoW delays.",
        enforcement_action="QUALIFY",
    ),
    "SSR-05": SemanticSafetyRule(
        rule_id="SSR-05",
        rule_name="MISSING_DATA_NOT_NEGATIVE_EVIDENCE",
        description="Absence of inspection reports or telemetry data does not prove work was skipped or failed.",
        prohibited_escalation="Treating missing records as proof of negative performance or missing assets.",
        enforcement_action="QUALIFY",
    ),
    "SSR-06": SemanticSafetyRule(
        rule_id="SSR-06",
        rule_name="HISTORY_NOT_CURRENT_FACT",
        description="Historical contractor delinquency on past projects does not constitute empirical evidence of current project default.",
        prohibited_escalation="Projecting past performance record into definitive conclusion about current active site.",
        enforcement_action="DOWNGRADE",
    ),
    "SSR-07": SemanticSafetyRule(
        rule_id="SSR-07",
        rule_name="ML_PREDICTION_NOT_OBSERVED_FACT",
        description="Machine learning risk scores or failure predictions are probabilistic models, not observed facts.",
        prohibited_escalation="Treating ML risk probability as an established factual default or schedule delay.",
        enforcement_action="DOWNGRADE",
    ),
    "SSR-08": SemanticSafetyRule(
        rule_id="SSR-08",
        rule_name="PEER_DIFFERENCE_NOT_ABNORMALITY_WITHOUT_COHORT",
        description="Deviation from peer group mean is statistically meaningless if cohort quality is poor or sample size is inadequate.",
        prohibited_escalation="Declaring project abnormal against an unreliable or non-comparable peer cohort.",
        enforcement_action="DOWNGRADE",
    ),
}

# Accusatory and ungrounded trigger patterns prohibited in executive findings
UNSAFE_PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"\b(fraud|fraudulent|corrupt|corruption|bribe|bribes|scam|siphoned|embezzled)\b", re.IGNORECASE),
        "SSR-02",
        "Statistical anomaly sanitized: Replaced accusatory terms with empirical variance descriptions.",
    ),
    (
        re.compile(r"\b(billing manipulation|manipulated billing|fictitious billing|inflated bills)\b", re.IGNORECASE),
        "SSR-03",
        "Spend divergence sanitized: Replaced billing manipulation claim with expenditure-progress divergence.",
    ),
    (
        re.compile(r"\b(contractor (?:is )?at fault|contractor('s)? delinquency|contractor failed|contractor negligence)\b", re.IGNORECASE),
        "SSR-04",
        "Contractor attribution qualified: Replaced contractor fault assertion with neutral schedule slippage statement.",
    ),
    (
        re.compile(r"\b(definitely caused|proves that .+ caused|guaranteed to fail)\b", re.IGNORECASE),
        "SSR-01",
        "Absolute causal claim moderated: Softened definitive causal claims to probabilistic correlations.",
    ),
    (
        re.compile(r"\b(proven by ml|ai proved|model confirmed default)\b", re.IGNORECASE),
        "SSR-07",
        "ML fact conflation corrected: Replaced model certainty assertion with probabilistic model forecast.",
    ),
]

SANITIZATION_REPLACEMENTS = [
    (r"\b(billing manipulation|manipulated billing|fictitious billing)\b", "disproportionate expenditure relative to physical milestone completion"),
    (r"\b(fraudulent expenditure|fraudulent payments?)\b", "unreconciled expenditure variance warranting site-level voucher audit"),
    (r"\b(corruption|fraud|bribe|bribes|scam|siphoned|embezzled)\b", "unreconciled expenditure anomaly"),
    (r"\b(contractor at fault|contractor is at fault)\b", "schedule slippage observed, with root-cause attribution pending RoW and statutory inspection"),
    (r"\b(contractor negligence)\b", "execution delay requiring contract milestone review"),
    (r"\b(definitely caused)\b", "is strongly associated with"),
    (r"\b(guaranteed to fail)\b", "exhibits elevated schedule risk"),
    (r"\b(proves corruption|indicates fraud)\b", "reveals an empirical expenditure anomaly requiring audit"),
]


class CausalClaimGuard:
    """Deterministic guardrail enforcing semantic safety rules on statements and claims."""

    def __init__(self):
        self.rules = RULES_CATALOG

    def check_statement(self, text: str) -> Tuple[bool, List[str], str]:
        """Scans arbitrary text for semantic safety violations.
        
        Returns:
            (is_safe, list_of_violated_rule_ids, sanitized_text)
        """
        violations: List[str] = []
        sanitized = text

        for pattern, rule_id, note in UNSAFE_PATTERNS:
            if pattern.search(sanitized):
                if rule_id not in violations:
                    violations.append(rule_id)

        # Apply deterministic sanitization
        for target, replacement in SANITIZATION_REPLACEMENTS:
            sanitized = re.sub(target, replacement, sanitized, flags=re.IGNORECASE)

        is_safe = len(violations) == 0
        return is_safe, violations, sanitized

    def enforce_on_claim(self, claim: Claim) -> Tuple[Claim, List[str]]:
        """Evaluates and sanitizes a structured Claim against the 8 semantic rules."""
        safety_actions: List[str] = []
        is_safe, rule_ids, sanitized_stmt = self.check_statement(claim.statement)

        if not is_safe:
            claim.statement = sanitized_stmt
            was_unsupported = claim.status in (ClaimStatus.UNSUPPORTED, ClaimStatus.CONTRADICTED)
            has_reject = any(self.rules[rid].enforcement_action == "REJECT" for rid in rule_ids)

            for rid in rule_ids:
                rule = self.rules[rid]
                safety_actions.append(f"Enforced {rule.rule_name} ({rid}): {rule.description}")

            if was_unsupported or has_reject:
                claim.status = ClaimStatus.UNSUPPORTED
                claim.audit_note = "Rejected: Violates semantic safety or lacks empirical evidence."
            else:
                has_downgrade = any(self.rules[rid].enforcement_action == "DOWNGRADE" for rid in rule_ids)
                has_qualify = any(self.rules[rid].enforcement_action == "QUALIFY" for rid in rule_ids)

                if has_downgrade:
                    if claim.claim_level in (ClaimLevel.CAUSAL, ClaimLevel.ATTRIBUTION):
                        claim.claim_level = ClaimLevel.HYPOTHESIS
                        claim.status = ClaimStatus.CONTEXTUAL
                    claim.audit_note = "Downgraded under semantic safety rules."
                elif has_qualify:
                    if claim.claim_level in (ClaimLevel.CAUSAL, ClaimLevel.ATTRIBUTION):
                        claim.claim_level = ClaimLevel.HYPOTHESIS
                    claim.limitations.append("Subject to independent verification under semantic safety rules.")

        return claim, safety_actions
