"""Explicit peer matching. Peer deviation is contextual, not causal."""

from typing import Any, Dict, List, Optional
import statistics
import uuid

from app.domain.entities import PeerAnalysis
from app.domain.enums import CohortQuality, EventType, PeerClassification
from app.repositories import peer_analyses_repo, projects_repo

DEFAULT_WEIGHTS = {
    "sector": 3.0,
    "project_type": 2.0,
    "implementing_agency": 1.5,
    "state": 1.0,
    "cost_band": 1.5,
    "progress_stage": 1.0,
}

MIN_COHORT = 5
QUALITY_HIGH = 12
QUALITY_MODERATE = 8
QUALITY_WEAK = 3


def _num(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _cost_band(project: Dict[str, Any]) -> Optional[str]:
    cost = project.get("cost") if isinstance(project.get("cost"), dict) else {}
    revised = _num(cost.get("revised") or cost.get("original"))
    if revised is None:
        return None
    if revised < 500:
        return "lt_500"
    if revised < 2000:
        return "500_2000"
    if revised < 5000:
        return "2000_5000"
    return "gt_5000"


def _progress_stage(project: Dict[str, Any]) -> Optional[str]:
    phys = _num(project.get("physical_progress_pct") or project.get("physical_progress"))
    if phys is None:
        return None
    if phys < 25:
        return "early"
    if phys < 75:
        return "mid"
    return "late"


def _agency(project: Dict[str, Any]) -> Optional[str]:
    meta = project.get("metadata") if isinstance(project.get("metadata"), dict) else {}
    return meta.get("implementing_agency") or project.get("department") or project.get("implementing_agency")


def similarity_score(target: Dict[str, Any], candidate: Dict[str, Any], weights: Dict[str, float]) -> float:
    score = 0.0
    if target.get("sector") and target.get("sector") == candidate.get("sector"):
        score += weights.get("sector", 0)
    t_type = (target.get("metadata") or {}).get("project_type") if isinstance(target.get("metadata"), dict) else None
    c_type = (candidate.get("metadata") or {}).get("project_type") if isinstance(candidate.get("metadata"), dict) else None
    if t_type and t_type == c_type:
        score += weights.get("project_type", 0)
    if _agency(target) and _agency(target) == _agency(candidate):
        score += weights.get("implementing_agency", 0)
    if target.get("state") and target.get("state") == candidate.get("state"):
        score += weights.get("state", 0)
    if _cost_band(target) and _cost_band(target) == _cost_band(candidate):
        score += weights.get("cost_band", 0)
    if _progress_stage(target) and _progress_stage(target) == _progress_stage(candidate):
        score += weights.get("progress_stage", 0)
    return score


def cohort_quality(size: int, median_similarity: float) -> CohortQuality:
    if size < QUALITY_WEAK:
        return CohortQuality.INSUFFICIENT
    if size >= QUALITY_HIGH and median_similarity >= 5.0:
        return CohortQuality.HIGH_QUALITY
    if size >= QUALITY_MODERATE:
        return CohortQuality.MODERATE
    return CohortQuality.WEAK


def percentile(sorted_values: List[float], p: float) -> Optional[float]:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return round(sorted_values[0], 1)
    k = (len(sorted_values) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return round(sorted_values[f], 1)
    return round(sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f), 1)


def classify_peer_context(
    target_dphis: Optional[float],
    peer_scores: List[float],
    quality: CohortQuality,
) -> PeerClassification:
    if quality == CohortQuality.INSUFFICIENT or target_dphis is None or len(peer_scores) < QUALITY_WEAK:
        return PeerClassification.INSUFFICIENT_PEER_EVIDENCE
    median = statistics.median(peer_scores)
    high_share = sum(1 for s in peer_scores if s >= 65.0) / len(peer_scores)
    deviation = target_dphis - median
    if high_share >= 0.6 and target_dphis >= 65:
        return PeerClassification.COHORT_WIDE_DETERIORATION
    if deviation >= 15:
        return PeerClassification.PROJECT_SPECIFIC_OUTLIER
    if abs(deviation) < 8:
        return PeerClassification.SIMILAR_TO_COHORT
    return PeerClassification.UNCLEAR


async def analyze_peers(project: Dict[str, Any], current_dphis: Optional[float] = None) -> PeerAnalysis:
    project_id = project.get("project_id")
    dphis = current_dphis if current_dphis is not None else _num(project.get("current_dphis") or project.get("dphis"))
    candidates = await projects_repo.find_many({"project_id": {"$ne": project_id}}, limit=500)
    scored = []
    for cand in candidates:
        sim = similarity_score(project, cand, DEFAULT_WEIGHTS)
        if sim <= 0:
            continue
        scored.append((sim, cand))
    scored.sort(key=lambda item: item[0], reverse=True)
    included = [(sim, cand) for sim, cand in scored if sim >= 3.0][:40]
    peer_scores = []
    for _, cand in included:
        val = _num(cand.get("current_dphis") or cand.get("dphis"))
        if val is not None:
            peer_scores.append(val)
    size = len(included)
    median_sim = statistics.median([s for s, _ in included]) if included else 0.0
    quality = cohort_quality(size, float(median_sim))
    matching = []
    for key, label in (
        ("sector", "sector"),
        ("state", "state"),
        ("implementing_agency", "implementing_agency"),
        ("cost_band", "cost_band"),
        ("progress_stage", "progress_stage"),
    ):
        matching.append(label)

    if quality == CohortQuality.INSUFFICIENT:
        analysis = PeerAnalysis(
            peer_analysis_id=f"PEER-{uuid.uuid4().hex[:10].upper()}",
            project_id=project_id,
            cohort_id=f"COH-{project.get('sector', 'NA')}",
            cohort_size=size,
            cohort_quality=quality,
            matching_factors=matching,
            matching_criteria={
                "sector": project.get("sector"),
                "state": project.get("state"),
                "cost_band": _cost_band(project),
                "progress_stage": _progress_stage(project),
                "weights": DEFAULT_WEIGHTS,
            },
            benchmarks=None,
            deviations=None,
            trajectory_summary=None,
            classification=PeerClassification.INSUFFICIENT_PEER_EVIDENCE,
            availability=False,
            reason="insufficient_peer_data",
        )
        await peer_analyses_repo.insert_one(analysis.model_dump())
        return analysis

    sorted_scores = sorted(peer_scores)
    median = round(statistics.median(sorted_scores), 1) if sorted_scores else None
    p75 = percentile(sorted_scores, 0.75)
    p90 = percentile(sorted_scores, 0.90)
    deviation = round(dphis - median, 1) if dphis is not None and median is not None else None
    classification = classify_peer_context(dphis, peer_scores, quality)
    analysis = PeerAnalysis(
        peer_analysis_id=f"PEER-{uuid.uuid4().hex[:10].upper()}",
        project_id=project_id,
        cohort_id=f"COH-{project.get('sector', 'NA')}",
        cohort_size=size,
        cohort_quality=quality,
        matching_factors=matching,
        matching_criteria={
            "sector": project.get("sector"),
            "state": project.get("state"),
            "cost_band": _cost_band(project),
            "progress_stage": _progress_stage(project),
            "implementing_agency": _agency(project),
            "weights": DEFAULT_WEIGHTS,
        },
        benchmarks={
            "peer_median_dphis": median,
            "peer_p75_dphis": p75,
            "peer_p90_dphis": p90,
            "target_dphis": dphis,
        },
        deviations={
            "peer_deviation": deviation,
            "classification": classification.value,
        },
        trajectory_summary="Peer trajectory comparison uses current DPHIS levels; historical peer series may be incomplete.",
        classification=classification,
        availability=True,
        reason=None,
    )
    await peer_analyses_repo.insert_one(analysis.model_dump())
    return analysis


def peer_event_payload(analysis: PeerAnalysis) -> Optional[Dict[str, Any]]:
    if not analysis.availability:
        return None
    if analysis.classification == PeerClassification.PROJECT_SPECIFIC_OUTLIER:
        return {
            "event_type": EventType.PEER_OUTLIER.value,
            "severity": "HIGH",
            "trigger_metrics": analysis.deviations or {},
        }
    if analysis.classification == PeerClassification.COHORT_WIDE_DETERIORATION:
        return {
            "event_type": EventType.COHORT_ANOMALY.value,
            "severity": "HIGH",
            "trigger_metrics": analysis.benchmarks or {},
        }
    return None
