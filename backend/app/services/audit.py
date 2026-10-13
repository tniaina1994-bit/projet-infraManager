from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ops import AuditLog


def log_action(
    db: Session,
    *,
    username: str,
    action: str,
    resource: str | None = None,
    resource_id: str | int | None = None,
    ip_address: str | None = None,
    result: str = "SUCCESS",
) -> AuditLog:
    entry = AuditLog(
        username=username,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=ip_address,
        result=result,
    )
    db.add(entry)
    db.commit()
    return entry
