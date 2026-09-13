from typing import Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class RiskComponents(BaseModel):
    time: float = Field(..., ge=0.0, le=1.0)
    cost: float = Field(..., ge=0.0, le=1.0)
    progress: float = Field(..., ge=0.0, le=1.0)
    milestone: float = Field(..., ge=0.0, le=1.0)
    financial: float = Field(..., ge=0.0, le=1.0)
    implementation: float = Field(..., ge=0.0, le=1.0)

class RiskTrend(BaseModel):
    previous: float
    current: float
    change_pts: float
    direction: str  # "WORSENING", "STABLE", "IMPROVING"

class DPHISScore(BaseModel):
    project_id: str
    dphis: float = Field(..., ge=0.0, le=100.0)
    level: RiskLevel
    components: RiskComponents
    trend: RiskTrend
    trend_multiplier: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
