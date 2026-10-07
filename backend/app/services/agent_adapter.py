"""Adapter boundary: Main Backend → AgentAdapter → existing PAIMANA agent.

Does not rewrite ML models or the investigation engine. Normalizes agent
output into stable domain objects for the application API.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

from app.config.logging import logger
from app.domain.entities import (
    Evidence,
    Hypothesis,
    Investigation,
    Prediction,
    Recommendation,
)
from app.domain.enums import (
    InvestigationStatus,
    RecommendationApprovalStatus,
    RecommendationValidationStatus,
    RiskTier,
    TerminationReason,
)
from app.domain.errors import DomainError, ErrorCode
from app.services.dphis_service import calculate_dphis
from app.services.feature_service import engineer_features
from app.services.shap_service import explain_features
from app.ml.models.cost_model import cost_model
from app.ml.models.delay_model import delay_model


def risk_tier_from_dphis(dphis: Optional[float]) -> Optional[RiskTier]:
    if dphis is None:
        return None
    if dphis >= 80:
        return RiskTier.CRITICAL
    if dphis >= 65:
        return RiskTier.HIGH
    if dphis >= 50:
        return RiskTier.MODERATE
    return RiskTier.LOW


def map_legacy_investigation_status(raw: Optional[str]) -> InvestigationStatus:
    if not raw:
        return InvestigationStatus.QUEUED
    value = str(raw).lower()
    mapping = {
        "pending_approval": InvestigationStatus.PENDING_APPROVAL,
        "awaiting decision": InvestigationStatus.READY_FOR_DECISION,
        "approved": InvestigationStatus.APPROVED,
        "rejected": InvestigationStatus.REJECTED,
        "investigating": InvestigationStatus.INVESTIGATING,
        "queued": InvestigationStatus.QUEUED,
        "failed": InvestigationStatus.FAILED,
        "concluded": InvestigationStatus.CONCLUDED,
    }
    return mapping.get(value, InvestigationStatus.INVESTIGATING)


class AgentAdapter:
    """Thin facade over existing feature engineering, models, SHAP, DPHIS, investigator."""

    def engineer(self, project: Dict[str, Any], snapshots: List[Dict[str, Any]]) -> Dict[str, float]:
        return engineer_features(project, snapshots)

    def predict(self, project_id: str, snapshot_id: Optional[str], features: Dict[str, Any]) -> Prediction:
        try:
            cost = cost_model.predict(features) or {}
            delay = delay_model.predict(features) or {}
            cost_overrun = cost.get("predicted_overrun_pct")
            if cost_overrun is None:
                cost_overrun = cost.get("cost_risk_score")
            slip = delay.get("expected_delay_months")
            if slip is None:
                slip = delay.get("time_risk_score")
            risk_score = None
            if isinstance(cost.get("cost_risk_score"), (int, float)) and isinstance(delay.get("time_risk_score"), (int, float)):
                risk_score = round((float(cost["cost_risk_score"]) + float(delay["time_risk_score"])) / 2.0 * 100.0, 1)
            available = cost_overrun is not None or slip is not None
            return Prediction(
                prediction_id=f"PRD-{uuid.uuid4().hex[:10].upper()}",
                project_id=project_id,
                snapshot_id=snapshot_id,
                model_version=str(cost.get("model_version") or delay.get("model_version") or "paimana_xgb_v1"),
                cost_overrun_prediction=float(cost_overrun) if isinstance(cost_overrun, (int, float)) else None,
                schedule_slippage_prediction=float(slip) if isinstance(slip, (int, float)) else None,
                risk_score=risk_score,
                combined_crosscheck={"cost": cost, "delay": delay},
                availability=available,
                reason=None if available else "prediction_unavailable",
            )
        except Exception as exc:
            logger.warning(f"AgentAdapter.predict failed: {exc}")
            return Prediction(
                prediction_id=f"PRD-{uuid.uuid4().hex[:10].upper()}",
                project_id=project_id,
                snapshot_id=snapshot_id,
                availability=False,
                reason="model_unavailable",
            )

    def explain(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            items = explain_features(features)
            return [item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in items]
        except Exception as exc:
            logger.warning(f"AgentAdapter.explain failed: {exc}")
            return []

    def score_dphis(
        self,
        project_id: str,
        features: Dict[str, Any],
        prediction: Optional[Prediction],
        previous_dphis: Optional[float],
    ):
        cost_risk = None
        time_risk = None
        if prediction and prediction.combined_crosscheck:
            cost_risk = (prediction.combined_crosscheck.get("cost") or {}).get("cost_risk_score")
            time_risk = (prediction.combined_crosscheck.get("delay") or {}).get("time_risk_score")
        return calculate_dphis(
            project_id=project_id,
            features=features,
            cost_risk=cost_risk,
            time_risk=time_risk,
            previous_dphis=previous_dphis,
        )

    async def investigate(self, project_id: str, trigger_reason: str) -> Investigation:
        try:
            from app.agents.investigator import run_investigation

            report = await run_investigation(project_id, trigger_reason=trigger_reason)
            return self.normalize_investigation(report, trigger_reason=trigger_reason)
        except Exception as exc:
            logger.error(f"AgentAdapter.investigate failed: {exc}", exc_info=True)
            raise DomainError(
                ErrorCode.AGENT_UNAVAILABLE,
                "Investigation engine is unavailable",
                http_status=503,
                details={"project_id": project_id},
            )

    def normalize_investigation(self, report: Any, trigger_reason: Optional[str] = None) -> Investigation:
        if hasattr(report, "model_dump"):
            raw = report.model_dump()
        elif isinstance(report, dict):
            raw = report
        else:
            raw = {}
        status = map_legacy_investigation_status(raw.get("status"))
        confidence = raw.get("overall_confidence")
        if confidence is not None:
            try:
                confidence = float(confidence)
            except (TypeError, ValueError):
                confidence = None
        findings = raw.get("findings") or []
        evidence_count = 0
        for finding in findings:
            evidence = finding.get("evidence") if isinstance(finding, dict) else getattr(finding, "evidence", [])
            evidence_count += len(evidence or [])
        return Investigation(
            investigation_id=raw.get("investigation_id") or f"INV-{uuid.uuid4().hex[:8].upper()}",
            project_id=raw.get("project_id") or "UNKNOWN",
            trigger_reason=raw.get("trigger_reason") or trigger_reason,
            status=status,
            confidence=confidence,
            started_at=raw.get("created_at") or datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc) if status != InvestigationStatus.INVESTIGATING else None,
            termination_reason=TerminationReason.DECISION_READINESS_REACHED
            if status in (InvestigationStatus.PENDING_APPROVAL, InvestigationStatus.READY_FOR_DECISION)
            else None,
            executive_summary=raw.get("executive_summary"),
            evidence_count=evidence_count,
            contradiction_count=0,
            tools_executed=list(raw.get("tools_executed") or []),
        )

    def normalize_evidence(self, investigation_id: str, report: Any) -> List[Evidence]:
        raw = report.model_dump() if hasattr(report, "model_dump") else (report or {})
        items: List[Evidence] = []
        for finding in raw.get("findings") or []:
            finding = finding if isinstance(finding, dict) else finding.model_dump()
            role = "supporting"
            for ev in finding.get("evidence") or []:
                ev = ev if isinstance(ev, dict) else ev.model_dump()
                items.append(
                    Evidence(
                        evidence_id=f"EVD-{uuid.uuid4().hex[:10].upper()}",
                        investigation_id=investigation_id,
                        source_type=ev.get("source") or "unknown",
                        source_id=None,
                        content=ev.get("value"),
                        field=ev.get("field"),
                        reliability=finding.get("confidence"),
                        role=role,
                    )
                )
        return items

    def normalize_hypotheses(self, investigation_id: str, report: Any) -> List[Hypothesis]:
        raw = report.model_dump() if hasattr(report, "model_dump") else (report or {})
        hypotheses = []
        for idx, finding in enumerate(raw.get("findings") or [], start=1):
            finding = finding if isinstance(finding, dict) else finding.model_dump()
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=f"HYP-{idx:02d}",
                    investigation_id=investigation_id,
                    statement=finding.get("title") or finding.get("summary") or "Unspecified hypothesis",
                    status="open",
                    support_score=finding.get("confidence"),
                    contradiction_score=None,
                    falsification_condition="Would be weakened by contradictory progress/expenditure evidence",
                )
            )
        return hypotheses

    def normalize_recommendations(self, investigation_id: str, report: Any) -> List[Recommendation]:
        raw = report.model_dump() if hasattr(report, "model_dump") else (report or {})
        recs = []
        for rec in raw.get("recommendations") or []:
            rec = rec if isinstance(rec, dict) else rec.model_dump()
            recs.append(
                Recommendation(
                    recommendation_id=f"REC-{uuid.uuid4().hex[:8].upper()}",
                    investigation_id=investigation_id,
                    statement=rec.get("action") or rec.get("statement") or "",
                    authority_required=rec.get("target_agency"),
                    validation_status=RecommendationValidationStatus.CANDIDATE,
                    approval_status=RecommendationApprovalStatus.PENDING_APPROVAL,
                    uncertainty="Heuristic investigation output; not a verified cause",
                )
            )
        return recs


agent_adapter = AgentAdapter()
