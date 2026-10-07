"""Asynchronous investigation orchestration.

HTTP requests must not wait on the full agent loop.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from app.config.logging import logger
from app.domain.enums import InvestigationStatus, RecommendationApprovalStatus
from app.domain.errors import DomainError, ErrorCode
from app.repositories import (
    evidence_repo,
    hypotheses_repo,
    interventions_repo,
    investigations_repo,
    outcomes_repo,
    recommendations_repo,
)
from app.services.agent_adapter import agent_adapter
from app.services.audit_service import record_audit


async def queue_investigation(project_id: str, trigger_reason: str, actor: str = "system") -> dict:
    investigation_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "investigation_id": investigation_id,
        "project_id": project_id,
        "trigger_reason": trigger_reason,
        "status": InvestigationStatus.QUEUED.value,
        "created_at": datetime.now(timezone.utc),
    }
    await investigations_repo.insert_one(doc)
    await record_audit(
        actor=actor,
        action="investigation.queued",
        target_type="investigation",
        target_id=investigation_id,
        new_value={"project_id": project_id, "trigger_reason": trigger_reason},
    )
    return doc


async def execute_queued_investigation(investigation_id: str) -> dict:
    existing = await investigations_repo.find_one({"investigation_id": investigation_id})
    if not existing:
        raise DomainError(ErrorCode.INVESTIGATION_NOT_FOUND, "Investigation not found", 404)
    await investigations_repo.update_one(
        {"investigation_id": investigation_id},
        {"status": InvestigationStatus.INVESTIGATING.value, "started_at": datetime.now(timezone.utc)},
    )
    try:
        from app.agents.investigator import run_investigation

        raw_report = await run_investigation(
            existing["project_id"],
            trigger_reason=existing.get("trigger_reason") or "QUEUED",
        )
        inv = agent_adapter.normalize_investigation(raw_report, trigger_reason=existing.get("trigger_reason"))
        evidence = agent_adapter.normalize_evidence(investigation_id, raw_report)
        hypotheses = agent_adapter.normalize_hypotheses(investigation_id, raw_report)
        recs = agent_adapter.normalize_recommendations(investigation_id, raw_report)
        for item in evidence:
            await evidence_repo.insert_one(item.model_dump())
        for item in hypotheses:
            await hypotheses_repo.insert_one(item.model_dump())
        for item in recs:
            await recommendations_repo.insert_one(item.model_dump())
        payload = {
            **inv.model_dump(),
            "investigation_id": investigation_id,
            "status": InvestigationStatus.READY_FOR_DECISION.value,
            "completed_at": datetime.now(timezone.utc),
            "legacy_report": raw_report.model_dump() if hasattr(raw_report, "model_dump") else {},
        }
        updated = await investigations_repo.update_one({"investigation_id": investigation_id}, payload)
        return updated or payload
    except Exception as exc:
        logger.error(f"Queued investigation failed: {exc}", exc_info=True)
        failed = await investigations_repo.update_one(
            {"investigation_id": investigation_id},
            {
                "status": InvestigationStatus.FAILED.value,
                "completed_at": datetime.now(timezone.utc),
                "termination_reason": "source_unavailable",
            },
        )
        return failed or existing


async def get_investigation_bundle(investigation_id: str) -> Dict[str, Any]:
    investigation = await investigations_repo.find_one({"investigation_id": investigation_id})
    if not investigation:
        raise DomainError(ErrorCode.INVESTIGATION_NOT_FOUND, "Investigation not found", 404)
    evidence = await evidence_repo.find_many({"investigation_id": investigation_id}, limit=200)
    hypotheses = await hypotheses_repo.find_many({"investigation_id": investigation_id}, limit=50)
    recs = await recommendations_repo.find_many({"investigation_id": investigation_id}, limit=50)
    return {
        "investigation": investigation,
        "evidence": evidence,
        "hypotheses": hypotheses,
        "recommendations": recs,
        "confidence_note": "Support scores are heuristic, not calibrated probabilities.",
    }


async def decide_investigation(
    investigation_id: str,
    *,
    approved: bool,
    actor: str,
    reason: Optional[str] = None,
) -> dict:
    existing = await investigations_repo.find_one({"investigation_id": investigation_id})
    if not existing:
        raise DomainError(ErrorCode.INVESTIGATION_NOT_FOUND, "Investigation not found", 404)
    if existing.get("status") in (InvestigationStatus.APPROVED.value, InvestigationStatus.REJECTED.value):
        raise DomainError(ErrorCode.CONFLICT, "Investigation already decided", 409)
    status = InvestigationStatus.APPROVED if approved else InvestigationStatus.REJECTED
    rec_status = RecommendationApprovalStatus.APPROVED if approved else RecommendationApprovalStatus.REJECTED
    recs = await recommendations_repo.find_many({"investigation_id": investigation_id}, limit=50)
    intervention = None
    if approved:
        rec = recs[0] if recs else {}
        intervention = {
            "intervention_id": f"INT-{uuid.uuid4().hex[:8].upper()}",
            "recommendation_id": rec.get("recommendation_id"),
            "investigation_id": investigation_id,
            "project_id": existing.get("project_id"),
            "approved_by": actor,
            "approved_at": datetime.now(timezone.utc),
            "execution_status": "pending",
            "action": rec.get("statement"),
        }
        await interventions_repo.insert_one(intervention)
    for rec in recs:
        await recommendations_repo.update_one(
            {"recommendation_id": rec.get("recommendation_id")},
            {"approval_status": rec_status.value},
        )
    updated = await investigations_repo.update_one(
        {"investigation_id": investigation_id},
        {
            "status": status.value,
            "approved_by": actor,
            "approved_at": datetime.now(timezone.utc),
            "decision_reason": reason,
        },
    )
    await record_audit(
        actor=actor,
        action="investigation.approve" if approved else "investigation.reject",
        target_type="investigation",
        target_id=investigation_id,
        old_value=existing.get("status"),
        new_value=status.value,
        reason=reason,
    )
    return {"investigation": updated, "intervention": intervention}


async def record_investigation_outcome(
    investigation_id: str,
    *,
    actor: str,
    notes: Optional[str] = None,
    after_metrics: Optional[dict] = None,
) -> dict:
    existing = await investigations_repo.find_one({"investigation_id": investigation_id})
    if not existing:
        raise DomainError(ErrorCode.INVESTIGATION_NOT_FOUND, "Investigation not found", 404)
    ints = await interventions_repo.find_many({"investigation_id": investigation_id}, limit=10)
    if not ints:
        raise DomainError(ErrorCode.INTERVENTION_NOT_FOUND, "No intervention exists for this investigation", 404)
    intervention = ints[0]
    outcome = {
        "outcome_id": f"OUT-{uuid.uuid4().hex[:8].upper()}",
        "intervention_id": intervention["intervention_id"],
        "recorded_at": datetime.now(timezone.utc),
        "before_metrics": {"dphis": existing.get("legacy_report", {}).get("dphis")},
        "after_metrics": after_metrics,
        "observed_change": after_metrics,
        "outcome_status": "recorded",
        "notes": notes,
        "recorded_by": actor,
    }
    await outcomes_repo.insert_one(outcome)
    await investigations_repo.update_one(
        {"investigation_id": investigation_id},
        {"status": InvestigationStatus.OUTCOME_RECORDED.value},
    )
    await record_audit(
        actor=actor,
        action="investigation.outcome",
        target_type="investigation",
        target_id=investigation_id,
        new_value=outcome,
        reason=notes,
    )
    return outcome
