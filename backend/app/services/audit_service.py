import uuid
from typing import Any, Optional
from app.domain.entities import AuditLog
from app.repositories import audit_logs_repo


async def record_audit(
    *,
    actor: str,
    action: str,
    target_type: str,
    target_id: str,
    old_value: Any = None,
    new_value: Any = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> dict:
    log = AuditLog(
        audit_id=f"AUD-{uuid.uuid4().hex[:12].upper()}",
        actor=actor or "system",
        action=action,
        target_type=target_type,
        target_id=target_id,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        request_id=request_id,
    )
    return await audit_logs_repo.insert_one(log.model_dump())
