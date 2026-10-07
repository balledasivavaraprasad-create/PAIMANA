"""Candidate Deduplicator for merging semantically identical recommendation candidates."""
from __future__ import annotations
import re
from typing import Tuple
from .candidate import RecommendationCandidate


class CandidateDeduplicator:
    """Detects and merges redundant recommendation candidates before validation and ranking."""

    def _tokenize(self, text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "this", "that", "from", "into", "over", "project", "prior", "action"}
        return {w for w in words if w not in stopwords}

    def deduplicate(
        self,
        candidates: list[RecommendationCandidate],
        similarity_threshold: float = 0.65
    ) -> list[RecommendationCandidate]:
        """Merges or filters near-duplicate candidates based on title and rationale token overlap."""
        if len(candidates) <= 1:
            return candidates

        unique_candidates: list[RecommendationCandidate] = []

        for cand in candidates:
            tokens_c = self._tokenize(cand.title + " " + cand.rationale)
            duplicate_found = False

            for existing in unique_candidates:
                tokens_e = self._tokenize(existing.title + " " + existing.rationale)
                if not tokens_c or not tokens_e:
                    continue

                jaccard = len(tokens_c & tokens_e) / len(tokens_c | tokens_e)
                if jaccard >= similarity_threshold:
                    # Merge evidence citations into existing candidate
                    duplicate_found = True
                    for eid in cand.evidence_ids:
                        if eid not in existing.evidence_ids:
                            existing.evidence_ids.append(eid)
                    for hid in cand.hypothesis_ids:
                        if hid not in existing.hypothesis_ids:
                            existing.hypothesis_ids.append(hid)
                    break

            if not duplicate_found:
                unique_candidates.append(cand)

        return unique_candidates
