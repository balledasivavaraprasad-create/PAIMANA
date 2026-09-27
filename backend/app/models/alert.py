from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class Alert(BaseModel):
    alert_id: str
    event_id: Optional[str] = None
    project_id: str
    project_name: str
    user_id: Optional[str] = None
    previous_dphis: Optional[float] = None
    current_dphis: Optional[float] = None
    threshold: Optional[float] = 70.0
    severity: str  # critical, high, moderate, low
    previous_severity: Optional[str] = None
    trigger: str = "DPHIS_THRESHOLD_CROSSED"  # backward compat
    trigger_type: str = "DPHIS_THRESHOLD_CROSSED"
    top_risk_reasons: List[str] = Field(default_factory=list)
    dphis: float  # current dphis score
    message: str
    status: str = "PENDING"  # PENDING, ACKNOWLEDGED, RESOLVED
    notification_status: str = "pending"  # pending, sent, failed
    user_notified: bool = False
    admin_notified: bool = False
    n8n_execution_reference: Optional[str] = None
    webhook_dispatched: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

