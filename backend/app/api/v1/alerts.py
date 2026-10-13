from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import INFRASTRUCTURE_READ, INFRASTRUCTURE_WRITE
from app.models.auth import User
from app.models.ops import Alert, NotificationChannel
from app.schemas import AlertOut, AlertUpdate, NotificationChannelCreate, NotificationChannelOut

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    status: str | None = Query(None),
    severity: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(INFRASTRUCTURE_READ)),
):
    stmt = select(Alert).order_by(Alert.timestamp.desc()).limit(500)
    if status:
        stmt = stmt.where(Alert.status == status)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    return db.scalars(stmt).all()


@router.patch("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(INFRASTRUCTURE_WRITE)),
):
    if payload.status not in {"NEW", "ACK", "RESOLVED"}:
        raise HTTPException(status_code=422, detail="Invalid alert status")
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = payload.status
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/notifications", response_model=list[NotificationChannelOut])
def list_channels(db: Session = Depends(get_db), _: User = Depends(require_permission(INFRASTRUCTURE_READ))):
    return db.scalars(select(NotificationChannel).order_by(NotificationChannel.id)).all()


@router.post("/notifications", response_model=NotificationChannelOut, status_code=201)
def create_channel(
    payload: NotificationChannelCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(INFRASTRUCTURE_WRITE)),
):
    if payload.type not in {"email", "telegram", "discord", "webhook"}:
        raise HTTPException(status_code=422, detail="Unsupported channel type")
    channel = NotificationChannel(**payload.model_dump())
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return channel
