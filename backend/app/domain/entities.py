from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.domain.enums import (
    AlertDeliveryStatus,
    AlertStatus,
    CohortQuality,
    DataFreshness,
    EventType,
    InvestigationStatus,
    InterventionExecutionStatus,
    OutcomeStatus,
    OutboxStatus,
    PeerClassification,
    RecommendationApprovalStatus,
    RecommendationValidationStatus,
    RiskTier,
    TerminationReason,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Project(BaseModel):
    project_id: str
    project_name: str
    ministry: Optional[str] = None
    department: Optional[str] = None
    sector: Optional[str] = None
    implementing_agency: Optional[str] = None
    state: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    cost: Optional[Dict[str, Any]] = None
    schedule: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    monitoring_status: Optional[str] = None
    last_observed_at: Optional[datetime] = None
    current_snapshot_id: Optional[str] = None
    assigned_users: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ProjectSnapshot(BaseModel):
    snapshot_id: str
    project_id: str
    observed_at: datetime
    report_period: Optional[str] = None
    source: str = "internal"
    source_record_id: Optional[str] = None
    snapshot_hash: str
    raw_payload_reference: Optional[str] = None
    quality_status: str = "unknown"
    physical_progress: Optional[float] = None
    financial_progress: Optional[float] = None
    cumulative_expenditure: Optional[float] = None
    milestones: Optional[Dict[str, Any]] = None
    weather: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=utcnow)


class Prediction(BaseModel):
    prediction_id: str
    project_id: str
    snapshot_id: Optional[str] = None
    model_version: Optional[str] = None
    cost_overrun_prediction: Optional[float] = None
    schedule_slippage_prediction: Optional[float] = None
    risk_score: Optional[float] = None
    combined_crosscheck: Optional[Dict[str, Any]] = None
    availability: bool = True
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class Event(BaseModel):
    event_id: str
    project_id: str
    snapshot_id: Optional[str] = None
    event_type: EventType
    severity: str
    trigger_metrics: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class Alert(BaseModel):
    alert_id: str
    event_id: Optional[str] = None
    project_id: str
    project_name: Optional[str] = None
    investigation_id: Optional[str] = None
    previous_dphis: Optional[float] = None
    current_dphis: Optional[float] = None
    threshold: Optional[float] = None
    severity: str
    trigger_type: str
    trigger_reason: Optional[str] = None
    status: AlertStatus = AlertStatus.PENDING
    delivery_status: AlertDeliveryStatus = AlertDeliveryStatus.QUEUED
    created_at: datetime = Field(default_factory=utcnow)
    acknowledged_at: Optional[datetime] = None


class Investigation(BaseModel):
    investigation_id: str
    project_id: str
    trigger_event_id: Optional[str] = None
    trigger_reason: Optional[str] = None
    status: InvestigationStatus = InvestigationStatus.QUEUED
    confidence: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    termination_reason: Optional[TerminationReason] = None
    executive_summary: Optional[str] = None
    evidence_count: int = 0
    contradiction_count: int = 0
    tools_executed: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class Evidence(BaseModel):
    evidence_id: str
    investigation_id: str
    source_type: str
    source_id: Optional[str] = None
    observed_at: Optional[datetime] = None
    freshness: Optional[DataFreshness] = None
    content: Any = None
    reliability: Optional[float] = None
    role: str = "observed"
    field: Optional[str] = None


class Hypothesis(BaseModel):
    hypothesis_id: str
    investigation_id: str
    statement: str
    status: str = "open"
    support_score: Optional[float] = None
    contradiction_score: Optional[float] = None
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    falsification_condition: Optional[str] = None


class Recommendation(BaseModel):
    recommendation_id: str
    investigation_id: str
    statement: str
    evidence_ids: List[str] = Field(default_factory=list)
    authority_required: Optional[str] = None
    validation_status: RecommendationValidationStatus = RecommendationValidationStatus.CANDIDATE
    approval_status: RecommendationApprovalStatus = RecommendationApprovalStatus.PENDING_APPROVAL
    expected_benefit: Optional[str] = None
    uncertainty: Optional[str] = None
    precedent_references: List[str] = Field(default_factory=list)


class Intervention(BaseModel):
    intervention_id: str
    recommendation_id: Optional[str] = None
    investigation_id: Optional[str] = None
    project_id: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    execution_status: InterventionExecutionStatus = InterventionExecutionStatus.PENDING
    executed_at: Optional[datetime] = None
    action: Optional[str] = None


class InterventionOutcome(BaseModel):
    outcome_id: str
    intervention_id: str
    recorded_at: datetime = Field(default_factory=utcnow)
    before_metrics: Optional[Dict[str, Any]] = None
    after_metrics: Optional[Dict[str, Any]] = None
    observed_change: Optional[Dict[str, Any]] = None
    outcome_status: OutcomeStatus = OutcomeStatus.RECORDED
    notes: Optional[str] = None


class PeerAnalysis(BaseModel):
    peer_analysis_id: str
    project_id: str
    cohort_id: Optional[str] = None
    cohort_size: int = 0
    cohort_quality: CohortQuality = CohortQuality.INSUFFICIENT
    matching_factors: List[str] = Field(default_factory=list)
    matching_criteria: Dict[str, Any] = Field(default_factory=dict)
    benchmarks: Optional[Dict[str, Any]] = None
    deviations: Optional[Dict[str, Any]] = None
    trajectory_summary: Optional[str] = None
    classification: PeerClassification = PeerClassification.INSUFFICIENT_PEER_EVIDENCE
    availability: bool = True
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class DataQuality(BaseModel):
    data_quality_id: str
    project_id: str
    snapshot_id: Optional[str] = None
    freshness: DataFreshness = DataFreshness.UNAVAILABLE
    missing_fields: List[str] = Field(default_factory=list)
    stale: bool = False
    quality_status: str = "unknown"
    last_observed_at: Optional[datetime] = None
    notes: Optional[str] = None


class AuditLog(BaseModel):
    audit_id: str
    actor: str
    action: str
    target_type: str
    target_id: str
    timestamp: datetime = Field(default_factory=utcnow)
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    reason: Optional[str] = None
    request_id: Optional[str] = None


class NotificationDelivery(BaseModel):
    delivery_id: str
    alert_id: Optional[str] = None
    event_id: Optional[str] = None
    channel: str = "n8n"
    status: AlertDeliveryStatus = AlertDeliveryStatus.QUEUED
    recipient_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    last_error: Optional[str] = None


class ModelMetadata(BaseModel):
    model_id: str
    name: str
    version: Optional[str] = None
    status: str = "unknown"
    last_loaded_at: Optional[datetime] = None
    availability: bool = True
    reason: Optional[str] = None


class MonitoringCycle(BaseModel):
    cycle_id: str
    trigger: str
    status: str = "running"
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: Optional[datetime] = None
    projects_evaluated: int = 0
    projects_skipped_no_change: int = 0
    events_generated: int = 0
    alerts_generated: int = 0
    investigations_triggered: int = 0
    failures: int = 0


class UserAccount(BaseModel):
    user_id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    product_roles: List[str] = Field(default_factory=list)
    assigned_projects: List[str] = Field(default_factory=list)
    is_active: bool = True


class RiskCurrent(BaseModel):
    dphis: Optional[float] = None
    risk_tier: Optional[RiskTier] = None
    predicted_cost_overrun_pct: Optional[float] = None
    predicted_schedule_slippage_months: Optional[float] = None
    availability: bool = True
    reason: Optional[str] = None


class MonitoringEvaluation(BaseModel):
    project_id: str
    snapshot_id: Optional[str] = None
    snapshot_hash: Optional[str] = None
    material_change: bool
    skipped_reason: Optional[str] = None
    prediction: Optional[Prediction] = None
    shap_drivers: List[Dict[str, Any]] = Field(default_factory=list)
    dphis: Optional[float] = None
    previous_dphis: Optional[float] = None
    risk_tier: Optional[str] = None
    events: List[Event] = Field(default_factory=list)
    peer_analysis: Optional[PeerAnalysis] = None
    data_quality: Optional[DataQuality] = None
    investigation_id: Optional[str] = None
    alert_ids: List[str] = Field(default_factory=list)
