"""Hypothesis Semantic Similarity & Deduplication Checker.

Detects semantic overlap, duplicate assertions, and parent-child refinement opportunities
to prevent redundant hypothesis sprawl.
"""
from __future__ import annotations
import re
from typing import Optional
from .model import Hypothesis


class HypothesisSimilarityChecker:
    """Computes semantic overlap between hypotheses to enforce novelty thresholds."""

    # Domain synonyms to normalize semantic matching
    SYNONYM_GROUPS = [
        {"contractor", "agency", "vendor", "concessionaire", "supplier"},
        {"delay", "slippage", "lag", "bottleneck", "stall", "slowdown"},
        {"expenditure", "spending", "disbursement", "billing", "cost", "funds"},
        {"clearance", "approval", "row", "land", "acquisition", "statutory", "regulatory"},
        {"reporting", "mpr", "data", "discrepancy", "inconsistency"},
        {"procurement", "tender", "bidding", "contract", "award"},
    ]

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        normalized = set()
        for w in words:
            mapped = w
            for syn_group in self.SYNONYM_GROUPS:
                if w in syn_group:
                    mapped = sorted(syn_group)[0]  # canonical representative
                    break
            normalized.add(mapped)
        return normalized

    def calculate_similarity(self, h1: Hypothesis, h2: Hypothesis) -> float:
        """Computes normalized Jaccard semantic overlap between two hypotheses."""
        s1 = f"{h1.statement} {h1.mechanism}"
        s2 = f"{h2.statement} {h2.mechanism}"
        t1 = self._tokenize(s1)
        t2 = self._tokenize(s2)
        if not t1 or not t2:
            return 0.0
        intersection = t1.intersection(t2)
        union = t1.union(t2)
        return len(intersection) / len(union)

    def find_most_similar(self, candidate: Hypothesis, existing: list[Hypothesis]) -> tuple[Optional[Hypothesis], float]:
        """Finds the existing hypothesis most similar to candidate."""
        best_match = None
        best_sim = 0.0
        for h in existing:
            if h.id == candidate.id:
                continue
            sim = self.calculate_similarity(candidate, h)
            if sim > best_sim:
                best_sim = sim
                best_match = h
        return best_match, round(best_sim, 3)

    def is_duplicate(self, candidate: Hypothesis, existing: list[Hypothesis], threshold: float = 0.70) -> tuple[bool, Optional[Hypothesis]]:
        """Returns True if candidate is semantically redundant with an existing hypothesis."""
        match, score = self.find_most_similar(candidate, existing)
        if match and score >= threshold:
            return True, match
        return False, None

    def is_refinement(self, candidate: Hypothesis, existing: list[Hypothesis], threshold: float = 0.45) -> tuple[bool, Optional[Hypothesis]]:
        """Returns True if candidate is a specific refinement of a broader existing hypothesis."""
        match, score = self.find_most_similar(candidate, existing)
        if match and score >= threshold and len(candidate.statement) > len(match.statement):
            return True, match
        return False, None
