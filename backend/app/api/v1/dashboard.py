from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import INFRASTRUCTURE_READ
from app.models.auth import User
from app.models.ops import AuditLog
from app.models.backup import BackupHistory, VeeamServer, BackupRepository
from app.models.infra import Container, Datacenter, Node, Storage, VM
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _count(db: Session, model) -> int:
    return db.scalar(select(func.count()).select_from(model)) or 0


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(require_permission(INFRASTRUCTURE_READ))):
    nodes_online = db.scalar(select(func.count()).select_from(Node).where(Node.status == "online")) or 0
    nodes_offline = db.scalar(select(func.count()).select_from(Node).where(Node.status != "online")) or 0
    vms_running = db.scalar(select(func.count()).select_from(VM).where(VM.status == "running")) or 0
    vms_stopped = db.scalar(select(func.count()).select_from(VM).where(VM.status != "running")) or 0

    from app.services.sync import get_threshold
    from app.core.config import settings as app_settings

    warn_pct = get_threshold(db, "storage_warning_threshold", app_settings.storage_warning_threshold)
    storage_warnings = db.scalar(
        select(func.count())
        .select_from(Storage)
        .where(Storage.total_gb > 0, Storage.used_gb >= Storage.total_gb * warn_pct / 100.0)
    ) or 0
    backup_failures = db.scalar(select(func.count()).select_from(BackupHistory).where(BackupHistory.status == "FAILED")) or 0
    backup_warnings = db.scalar(select(func.count()).select_from(BackupHistory).where(BackupHistory.status == "WARNING")) or 0
    running_backups = db.scalar(select(func.count()).select_from(BackupHistory).where(BackupHistory.status == "RUNNING")) or 0
    last_success = db.scalar(
        select(func.max(BackupHistory.ended_at)).where(BackupHistory.status == "SUCCESS")
    )

    activity = [
        {"user": a.username, "action": a.action, "resource": a.resource, "at": a.timestamp.isoformat()}
        for a in db.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(10)).all()
    ]

    return DashboardSummary(
        datacenters=_count(db, Datacenter),
        nodes=_count(db, Node),
        vms=_count(db, VM),
        containers=_count(db, Container),
        veeam_servers=_count(db, VeeamServer),
        backup_repositories=_count(db, BackupRepository),
        nodes_online=nodes_online,
        nodes_offline=nodes_offline,
        vms_running=vms_running,
        vms_stopped=vms_stopped,
        storage_warnings=storage_warnings,
        backup_failures=backup_failures,
        backup_warnings=backup_warnings,
        last_successful_backup=last_success,
        running_backups=running_backups,
        recent_activity=activity,
    )
