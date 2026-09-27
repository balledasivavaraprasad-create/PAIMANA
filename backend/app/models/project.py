from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime

class Location(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    district: str
    state: str

class Cost(BaseModel):
    original: float = Field(..., gt=0, description="Original estimated cost in Crores")
    revised: float = Field(..., gt=0, description="Revised sanctioned cost in Crores")
    currency: str = "INR_CR"

class Schedule(BaseModel):
    original_start: str
    original_end: str
    revised_end: str

class ProjectBase(BaseModel):
    project_id: str
    project_name: str
    ministry: str
    department: str
    sector: str
    state: str
    location: Location
    cost: Cost
    schedule: Schedule
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dphis: Optional[float] = 50.0
    risk_level: Optional[str] = "moderate"
    data_quality_score: Optional[float] = 95.0
    assigned_users: List[str] = Field(default_factory=list)
    dphis_threshold: Optional[float] = 70.0
    threshold_enabled: Optional[bool] = True
    threshold_source: Optional[str] = "project_creator"
    threshold_configured_by: Optional[str] = None
    threshold_configured_at: Optional[datetime] = None
    threshold_updated_at: Optional[datetime] = None
    threshold_status: Optional[str] = "below"
    previous_dphis: Optional[float] = None
    current_dphis: Optional[float] = None
    threshold_last_crossed_at: Optional[datetime] = None
    last_threshold_alert_id: Optional[str] = None
    threshold_history: List[Dict[str, Any]] = Field(default_factory=list)

class ProjectCreate(ProjectBase):
    pass

class ProjectThresholdUpdate(BaseModel):
    dphis_threshold: float = Field(..., ge=1.0, le=100.0, description="DPHIS score at which this project should trigger an alert")
    threshold_enabled: Optional[bool] = True
    configured_by: Optional[str] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    ministry: Optional[str] = None
    department: Optional[str] = None
    sector: Optional[str] = None
    state: Optional[str] = None
    location: Optional[Location] = None
    cost: Optional[Cost] = None
    schedule: Optional[Schedule] = None
    metadata: Optional[Dict[str, Any]] = None
    dphis: Optional[float] = None
    risk_level: Optional[str] = None
    data_quality_score: Optional[float] = None
    assigned_users: Optional[List[str]] = None
    dphis_threshold: Optional[float] = None
    threshold_enabled: Optional[bool] = None
    threshold_source: Optional[str] = None
    threshold_configured_by: Optional[str] = None
    threshold_status: Optional[str] = None

class ProjectInDB(ProjectBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
