"""Real SHAP explainability for the risk-score model (PAIMANA architecture review, problem #5).

The old `explain.drivers()` is rule-based (hand-written thresholds), which the review
correctly points out is not SHAP. This module adds actual SHAP attributions on top of
the risk model and keeps the rule-based drivers as the plain-language layer underneath
them, so an audit trail of "why" always exists even if SHAP is slow/unavailable.

The risk model is an sklearn Pipeline (preprocessing + a HistGradientBoosting
VotingRegressor wrapped in a TransformedTargetRegressor), not a bare tree model, so we
use a model-agnostic `shap.Explainer` over the pipeline's own `.predict`, with a small
background sample. This is slower than shap.TreeExplainer but works for any pipeline
and needs no knowledge of its internals -- important since the three models were
trained independently and may change shape.
"""
from __future__ import annotations
import logging
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

_explainer_cache: dict[int, tuple] = {}


def _encode(bg: pd.DataFrame, feature_cols: list[str]):
    """shap's default (Independent) masker does numeric ops (np.isclose) on every
    column, which breaks on the pipeline's raw string columns (ministry/sector). We
    factor those to integer codes for SHAP's purposes only, and wrap the model's
    predict so it decodes them back to strings before calling the real pipeline --
    the model itself is never touched, only what SHAP sees."""
    cat_cols = [c for c in feature_cols if not pd.api.types.is_numeric_dtype(bg[c])]
    code_maps = {c: {v: i for i, v in enumerate(sorted(bg[c].dropna().unique().tolist()))} for c in cat_cols}
    inv_maps = {c: {i: v for v, i in m.items()} for c, m in code_maps.items()}
    bg_num = bg.copy()
    for c in cat_cols:
        bg_num[c] = bg[c].map(code_maps[c]).fillna(-1)
    return bg_num.astype(float), cat_cols, code_maps, inv_maps


def _make_numeric_predict(model, feature_cols: list[str], cat_cols: list[str], inv_maps: dict):
    def _predict(arr: np.ndarray) -> np.ndarray:
        X = pd.DataFrame(arr, columns=feature_cols)
        for c in cat_cols:
            inv = inv_maps[c]
            fallback = next(iter(inv.values())) if inv else "Unknown"
            X[c] = X[c].round().astype(int).map(lambda code: inv.get(code, fallback))
        return model.predict(X)
    return _predict


def _get_explainer(model, feature_cols: list[str], background: pd.DataFrame):
    key = id(model)
    if key not in _explainer_cache:
        import shap  # imported lazily: heavy, optional dependency
        bg = background[feature_cols].sample(min(30, len(background)), random_state=42) \
            if len(background) > 30 else background[feature_cols]
        bg_num, cat_cols, code_maps, inv_maps = _encode(bg, feature_cols)
        f = _make_numeric_predict(model, feature_cols, cat_cols, inv_maps)
        explainer = shap.Explainer(f, bg_num, algorithm="permutation")
        _explainer_cache[key] = (explainer, cat_cols, code_maps)
    return _explainer_cache[key]


def shap_top_features(model, feats: dict, feature_cols: list[str], background: pd.DataFrame,
                       top_n: int = 5, max_evals: int = 200) -> Optional[list[dict]]:
    """Returns [{"feature": ..., "value": ..., "shap": ...}, ...] sorted by |shap| desc,
    or None if SHAP isn't installed / the explanation fails (caller falls back to the
    rule-based drivers only -- SHAP is an enrichment, never a hard dependency)."""
    try:
        X = pd.DataFrame([{c: feats.get(c) for c in feature_cols}], columns=feature_cols)
        X_display = X.replace([np.inf, -np.inf], np.nan)
        explainer, cat_cols, code_maps = _get_explainer(model, feature_cols, background)
        X_num = X_display.copy()
        for c in cat_cols:
            m = code_maps[c]
            fallback = next(iter(m.values())) if m else 0
            X_num[c] = X_num[c].map(m).fillna(fallback)
        X_num = X_num.astype(float)
        sv = explainer(X_num, max_evals=max_evals, silent=True)
        vals = np.asarray(sv.values)[0]
        order = np.argsort(-np.abs(vals))[:top_n]
        return [{"feature": feature_cols[i], "value": X_display.iloc[0, i], "shap": float(vals[i])} for i in order]
    except Exception as ex:  # pragma: no cover - shap missing or slow model, never break the pipeline
        log.info("SHAP explanation unavailable (%s); using rule-based drivers only", ex)
        return None


_LABELS = {
    "progress_expenditure_gap_pct": "expenditure running ahead of physical progress",
    "expenditure_original_cost_pct": "cumulative expenditure vs original cost",
    "schedule_slippage_months": "months already slipped on the completion date",
    "cost_overrun_pct": "cost revised up vs original sanction",
    "age_to_planned_ratio": "project age vs its planned duration",
    "progress_velocity_pct_per_month": "recent pace of physical progress",
    "remaining_work_rate": "work rate still needed to finish on the revised date",
    "burn_rate_ratio": "spending rate vs physical progress rate",
    "is_mega_project": "mega-project size (>= Rs 1,000 cr)",
    "remaining_progress_pct": "physical work still remaining",
}


def shap_summary_lines(top: list[dict]) -> list[str]:
    """Plain-language rendering of shap_top_features(), signed +/- like the doc's
    'WHY DID RISK CHANGE?' mock-up."""
    out = []
    for t in top:
        label = _LABELS.get(t["feature"], t["feature"].replace("_", " "))
        sign = "+" if t["shap"] >= 0 else "-"
        out.append(f"{sign}{abs(t['shap']):.1f} pts  {label} (value: {t['value']})")
    return out
