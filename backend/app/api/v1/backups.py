from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import BACKUP_READ
from app.models.auth import User
from app.models.backup import BackupHistory, BackupJob, BackupRepository
from app.schemas import BackupHistoryOut, BackupJobOut, BackupRepositoryOut

router = APIRouter(prefix="/backups", tags=["backups"])


@router.get("/jobs", response_model=list[BackupJobOut])
def list_jobs(
    status: str | None = Query(None),
    server: str | None = Query(None),
    environment: str | None = Query(None),
    backup_type: str | None = Query(None),
    date_from: datetime | None = Query(None),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(BACKUP_READ)),
):
    stmt = select(BackupJob).order_by(BackupJob.id.desc())
    if status:
        stmt = stmt.where(BackupJob.status == status)
    if server:
        stmt = stmt.where(BackupJob.server == server)
    if environment:
        stmt = stmt.where(BackupJob.environment == environment)
    if backup_type:
        stmt = stmt.where(BackupJob.backup_type == backup_type)
    if date_from:
        stmt = stmt.where(BackupJob.last_run_at >= date_from)
    if search:
        stmt = stmt.where(BackupJob.name.ilike(f"%{search}%"))
    return db.scalars(stmt.limit(500)).all()


@router.get("/history", response_model=list[BackupHistoryOut])
def list_history(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(BACKUP_READ)),
):
    stmt = select(BackupHistory).order_by(BackupHistory.started_at.desc().nullslast())
    if status:
        stmt = stmt.where(BackupHistory.status == status)
    return db.scalars(stmt.limit(500)).all()


@router.get("/repositories", response_model=list[BackupRepositoryOut])
def list_repositories(db: Session = Depends(get_db), _: User = Depends(require_permission(BACKUP_READ))):
    return db.scalars(select(BackupRepository).order_by(BackupRepository.name)).all()
