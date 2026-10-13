"""APScheduler background jobs (spec section 22): Proxmox ~30s, Veeam 1-5 min, configurable."""

from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import SessionLocal

scheduler = BackgroundScheduler(timezone="UTC")


def _sync_proxmox_job() -> None:
    from app.services.sync import sync_proxmox

    db = SessionLocal()
    try:
        sync_proxmox(db)
    except Exception:  # noqa: BLE001 — keep the scheduler thread alive
        pass
    finally:
        db.close()


def _sync_veeam_job() -> None:
    from app.services.sync import sync_veeam

    db = SessionLocal()
    try:
        sync_veeam(db)
    except Exception:  # noqa: BLE001
        pass
    finally:
        db.close()


def start_scheduler() -> None:
    if scheduler.running:
        return
    scheduler.add_job(
        _sync_proxmox_job,
        "interval",
        seconds=max(5, settings.proxmox_sync_seconds),
        id="sync_proxmox",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _sync_veeam_job,
        "interval",
        seconds=max(30, settings.veeam_sync_seconds),
        id="sync_veeam",
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
