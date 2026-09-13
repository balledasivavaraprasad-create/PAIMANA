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
    created_at: datetime = Field(default_factory=datetime.utcnow)
