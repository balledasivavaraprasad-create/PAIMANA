"""Codified Policy and Statutory Constraint Memory.

Maintains versioned institutional policies, statutory guidelines (GFR, MoRTH, CVC),
and hard operational limits that constrain recommendation and intervention logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PolicyConstraint:
    """A codified institutional policy or statutory guideline."""
    id: str
    title: str
    authority: str              # e.g., "GFR 2017", "MoRTH Circular 2023", "CVC"
    sector_scope: list[str]     # Empty list means universal
    contract_scope: list[str]   # e.g., ["EPC", "HAM"]
    rule_type: str              # "HARD_LIMIT", "STATUTORY_REQUIREMENT", "ADVISORY"
    description: str
    effective_date: str = "2020-01-01"
    is_active: bool = True

    def matches(self, sector: str, contract_type: str) -> bool:
        if not self.is_active:
            return False
        sec_match = not self.sector_scope or any(s.lower() in sector.lower() for s in self.sector_scope)
        cont_match = not self.contract_scope or any(c.lower() in contract_type.lower() for c in self.contract_scope)
        return sec_match and cont_match


class PolicyMemoryStore:
    """In-memory store of institutional policy constraints with scoping."""

    _DEFAULT_CONSTRAINTS = [
        PolicyConstraint(
            id="POL-GFR-ADVANCE",
            title="Mobilization Advance Cap",
            authority="GFR Rule 172(1)",
            sector_scope=[],
            contract_scope=["EPC", "Item Rate", "HAM"],
            rule_type="HARD_LIMIT",
            description="Mobilization advance shall not exceed 10% of contract value and must be backed by an unconditional bank guarantee."
        ),
        PolicyConstraint(
            id="POL-CVC-VARIATION",
            title="Contract Variation Ceiling",
            authority="CVC Guidelines on Contract Modifications",
            sector_scope=[],
            contract_scope=["EPC", "Item Rate"],
            rule_type="STATUTORY_REQUIREMENT",
            description="Variations exceeding 10% of original contract value require prior approval of the competent authority and detailed justification."
        ),
        PolicyConstraint(
            id="POL-MORTH-ROW-80",
            title="Prerequisite Land Availability",
            authority="MoRTH Guidelines for Highway EPC",
            sector_scope=["Road Transport and Highways"],
            contract_scope=["EPC"],
            rule_type="HARD_LIMIT",
            description="Appointed Date shall not be declared until at least 80% encumbrance-free contiguous Right-of-Way is physically acquired."
        ),
        PolicyConstraint(
            id="POL-DISPUTE-BOARD",
            title="Mandatory Conciliation Prior to Litigation",
            authority="Standard EPC Agreement Schedule C",
            sector_scope=["Road Transport and Highways", "Railways"],
            contract_scope=["EPC", "HAM"],
            rule_type="ADVISORY",
            description="All disputes must be referred to the Dispute Resolution Board (DRB) before invoking formal arbitration or court proceedings."
        ),
    ]

    def __init__(self, custom_constraints: Optional[list[PolicyConstraint]] = None):
        self._constraints = list(self._DEFAULT_CONSTRAINTS)
        if custom_constraints:
            self._constraints.extend(custom_constraints)

    def get_applicable_constraints(self, sector: str, contract_type: str) -> list[PolicyConstraint]:
        """Returns all active policy constraints applicable to given sector and contract."""
        return [c for c in self._constraints if c.matches(sector, contract_type)]
