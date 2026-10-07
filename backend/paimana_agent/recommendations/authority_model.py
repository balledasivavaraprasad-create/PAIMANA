"""Authority Model evaluating epistemic source authority and institutional governance alignment."""
from __future__ import annotations
from typing import Any, Optional


class AuthorityModel:
    """Calculates authority score based on source provenance and stakeholder governance level."""

    def compute_authority_score(
        self,
        cited_evidence_authority: float,
        approval_class: str,
        responsible_stakeholder: str,
        is_mega_project: bool = False
    ) -> tuple[float, dict[str, Any]]:
        """Evaluates authority score = 0.50 * source_authority + 0.50 * institutional_fit."""
        stakeholder_lower = responsible_stakeholder.lower()

        # Institutional fit evaluation
        if approval_class == "statutory":
            has_fit = any(k in stakeholder_lower for k in ["secretary", "apex", "ministry", "cabinet", "chief secretary"])
            fit_score = 0.95 if has_fit else 0.40
        elif approval_class == "executive":
            has_fit = any(k in stakeholder_lower for k in ["ministry", "chief engineer", "director", "advisor", "secretary"])
            fit_score = 0.90 if has_fit else 0.50
        elif approval_class == "managerial":
            has_fit = any(k in stakeholder_lower for k in ["project director", "engineer", "superintending", "pmu", "manager"])
            fit_score = 0.85 if has_fit else 0.60
        else: # routine
            fit_score = 0.80

        # Mega project scrutiny adjustment
        if is_mega_project and approval_class in ["executive", "statutory"] and fit_score < 0.80:
            fit_score = 0.30

        composite_authority = round(0.50 * cited_evidence_authority + 0.50 * fit_score, 3)
        composite_authority = max(0.10, min(1.0, composite_authority))

        breakdown = {
            "score": composite_authority,
            "source_authority": round(cited_evidence_authority, 3),
            "institutional_fit": round(fit_score, 3),
            "approval_class": approval_class,
            "responsible_stakeholder": responsible_stakeholder,
        }
        return composite_authority, breakdown
