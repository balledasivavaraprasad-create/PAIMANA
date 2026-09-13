from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class Alert(BaseModel):
    alert_id: str
    project_id: str
    project_name: str
    severity: str  # critical, high, moderate
    previous_severity: Optional[str] = None
    trigger: str  # DPHIS_ESCALATION, VELOCITY_STAGNATION, PHYSICAL_FINANCIAL_GAP
    dphis: float
    message: str
    status: str = "PENDING"  # PENDING, ACKNOWLEDGED, RESOLVED
    webhook_dispatched: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
