from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class OutboxEvent(BaseModel):
    outbox_id: str
    event_id: str
    event_type: str
    project_id: str
    target_url: str
    headers: Dict[str, str] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, dispatched, failed_retryable, dead_letter, duplicate
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    last_error: Optional[str] = None
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dispatched_at: Optional[datetime] = None
