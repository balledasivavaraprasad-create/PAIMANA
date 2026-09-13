from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class MilestoneData(BaseModel):
    completed: int = 0
    delayed: int = 0
    pending: int = 0
    total: int = 0

class WeatherSnapshot(BaseModel):
    rainfall_mm: float = 0.0
    temperature_c: float = 28.0
    wind_speed_kmh: float = 12.0
    disruption_flag: bool = False

class ProjectSnapshot(BaseModel):
    project_id: str
    snapshot_date: str  # YYYY-MM-DD
    physical_progress: float = Field(..., ge=0.0, le=100.0)
    financial_progress: float = Field(..., ge=0.0, le=100.0)
    cumulative_expenditure: float = Field(..., ge=0.0)
    milestones: MilestoneData = Field(default_factory=MilestoneData)
    weather: Optional[WeatherSnapshot] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SnapshotCreate(ProjectSnapshot):
    pass
