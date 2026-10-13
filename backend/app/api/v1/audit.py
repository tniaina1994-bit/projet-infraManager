from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import AUDIT_READ
from app.models.auth import User
from app.models.ops import AuditLog
from app.schemas import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])

# Spec section 20: audit logs must not be deletable by normal users.
# There is deliberately no DELETE endpoint — only ADMIN can purge, later, via ops tooling.


@router.get("", response_model=list[AuditLogOut])
def list_audit(
    username: str | None = Query(None),
    action: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(AUDIT_READ)),
):
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(500)
    if username:
        stmt = stmt.where(AuditLog.username == username)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    return db.scalars(stmt).all()
