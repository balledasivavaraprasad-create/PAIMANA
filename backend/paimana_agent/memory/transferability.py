"""Transferability Evaluation Engine.

Calculates the multi-dimensional transferability score between a historical
precedent context and the current investigation target. Prevents false positive
transfers (e.g., applying rural irrigation contract norms to metro rail projects).
"""
from __future__ import annotations
from typing import Optional
from .models import PrecedentContext


class TransferabilityEvaluator:
    """Evaluates how safely and accurately a precedent transfers to a target project."""

    SECTOR_AFFINITY = {
        ("Road Transport and Highways", "Railways"): 0.70,
        ("Road Transport and Highways", "Shipping"): 0.50,
        ("Power", "Renewable Energy"): 0.85,
        ("Power", "Coal"): 0.75,
        ("Urban Development", "Road Transport and Highways"): 0.60,
    }

    CONTRACT_AFFINITY = {
        ("EPC", "HAM"): 0.80,
        ("EPC", "Item Rate"): 0.50,
        ("EPC", "DBFOT"): 0.40,
        ("HAM", "DBFOT"): 0.75,
    }

    STAGE_AFFINITY = {
        ("Early (<25%)", "Mid (25-75%)"): 0.50,
        ("Mid (25-75%)", "Late (>75%)"): 0.60,
        ("Early (<25%)", "Late (>75%)"): 0.20,
    }

    COST_BAND_AFFINITY = {
        ("Mega (>1000Cr)", "Standard (150-1000Cr)"): 0.70,
        ("Standard (150-1000Cr)", "Minor (<150Cr)"): 0.60,
        ("Mega (>1000Cr)", "Minor (<150Cr)"): 0.30,
    }

    WEIGHTS = {
        "sector": 0.30,
        "contract": 0.20,
        "cost_band": 0.20,
        "stage": 0.15,
        "agency": 0.15,
    }

    @classmethod
    def evaluate(cls, precedent_ctx: PrecedentContext, target_ctx: PrecedentContext) -> float:
        """Computes transferability score in [0.0, 1.0]."""
        # 1. Sector Fit
        if precedent_ctx.sector.lower() == target_ctx.sector.lower():
            sec_fit = 1.0
        else:
            pair = (precedent_ctx.sector, target_ctx.sector)
            rev_pair = (target_ctx.sector, precedent_ctx.sector)
            sec_fit = cls.SECTOR_AFFINITY.get(pair, cls.SECTOR_AFFINITY.get(rev_pair, 0.30))

        # 2. Contract Fit
        if precedent_ctx.contract_type.upper() == target_ctx.contract_type.upper():
            cont_fit = 1.0
        else:
            pair = (precedent_ctx.contract_type, target_ctx.contract_type)
            rev_pair = (target_ctx.contract_type, precedent_ctx.contract_type)
            cont_fit = cls.CONTRACT_AFFINITY.get(pair, cls.CONTRACT_AFFINITY.get(rev_pair, 0.40))

        # 3. Cost Band Fit
        if precedent_ctx.cost_band == target_ctx.cost_band:
            cost_fit = 1.0
        else:
            pair = (precedent_ctx.cost_band, target_ctx.cost_band)
            rev_pair = (target_ctx.cost_band, precedent_ctx.cost_band)
            cost_fit = cls.COST_BAND_AFFINITY.get(pair, cls.COST_BAND_AFFINITY.get(rev_pair, 0.35))

        # 4. Stage Fit
        if precedent_ctx.stage_bracket == target_ctx.stage_bracket:
            stage_fit = 1.0
        else:
            pair = (precedent_ctx.stage_bracket, target_ctx.stage_bracket)
            rev_pair = (target_ctx.stage_bracket, precedent_ctx.stage_bracket)
            stage_fit = cls.STAGE_AFFINITY.get(pair, cls.STAGE_AFFINITY.get(rev_pair, 0.30))

        # 5. Agency Fit
        if precedent_ctx.implementing_agency and target_ctx.implementing_agency:
            if precedent_ctx.implementing_agency.lower() == target_ctx.implementing_agency.lower():
                agency_fit = 1.0
            else:
                agency_fit = 0.50
        else:
            agency_fit = 0.70  # Neutral if unknown

        score = (
            cls.WEIGHTS["sector"] * sec_fit +
            cls.WEIGHTS["contract"] * cont_fit +
            cls.WEIGHTS["cost_band"] * cost_fit +
            cls.WEIGHTS["stage"] * stage_fit +
            cls.WEIGHTS["agency"] * agency_fit
        )
        return round(min(1.0, max(0.0, score)), 3)
