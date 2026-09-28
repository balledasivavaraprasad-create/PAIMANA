from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class EvidenceItem(BaseModel):
    source: str  # e.g. "project_snapshot", "shap_model", "weather_api", "milestones"
    field: str   # e.g. "progress_velocity", "physical_financial_gap"
    value: Any
    context: Optional[str] = None

class Finding(BaseModel):
    title: str
    summary: str
    evidence: List[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)

class RecommendationItem(BaseModel):
    action: str
    reason: str
    priority: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    target_agency: Optional[str] = None

class InvestigationReport(BaseModel):
    investigation_id: str
    project_id: str
    trigger_reason: str
    executive_summary: str
    findings: List[Finding] = Field(default_factory=list)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    tools_executed: List[str] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.88, ge=0.0, le=1.0)
    status: str = "pending_approval"  # pending_approval, approved, rejected
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Intervention(BaseModel):
    intervention_id: str
    project_id: str
    investigation_id: str
    action: str
    recommendation: str
    approved_by: str
    approved_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, completed, closed
    outcome: Optional[str] = None
    outcome_recorded_at: Optional[datetime] = None
    outcome_metrics: Optional[Dict[str, Any]] = None

class InterventionApprovalRequest(BaseModel):
    approved_by: Optional[str] = "admin"
    notes: Optional[str] = None

class InterventionOutcomeRequest(BaseModel):
    outcome: str
    outcome_metrics: Optional[Dict[str, Any]] = None
    recorded_by: Optional[str] = None

class ProjectMemory(BaseModel):
    project_id: str
    risk_history: List[Dict[str, Any]] = Field(default_factory=list)
    detected_issues: List[str] = Field(default_factory=list)
    interventions: List[Dict[str, Any]] = Field(default_factory=list)
    outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

