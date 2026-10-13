from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Closed enum from spec section 12: SUCCESS WARNING FAILED RUNNING CANCELLED UNKNOWN


class BackupRepository(Base):
    __tablename__ = "backup_repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    type: Mapped[str | None] = mapped_column(String(64))
    total_capacity_gb: Mapped[float] = mapped_column(Float, default=0.0)
    used_gb: Mapped[float] = mapped_column(Float, default=0.0)
    free_gb: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN")
    last_backup_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def usage_percent(self) -> float:
        if not self.total_capacity_gb:
            return 0.0
        return round(self.used_gb / self.total_capacity_gb * 100, 1)


class BackupJob(Base):
    __tablename__ = "backup_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    source: Mapped[str | None] = mapped_column(String(255))
    target: Mapped[str | None] = mapped_column(String(255))
    schedule: Mapped[str | None] = mapped_column(String(128))
    retention: Mapped[str | None] = mapped_column(String(64))
    backup_type: Mapped[str | None] = mapped_column(String(64))
    environment: Mapped[str | None] = mapped_column(String(32))
    server: Mapped[str | None] = mapped_column(String(128))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    size_gb: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BackupHistory(Base):
    __tablename__ = "backup_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("backup_jobs.id", ondelete="SET NULL"), nullable=True)
    job_name: Mapped[str | None] = mapped_column(String(255))
    server: Mapped[str | None] = mapped_column(String(128))
    vm: Mapped[str | None] = mapped_column(String(128))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    backup_size_gb: Mapped[float] = mapped_column(Float, default=0.0)
    transferred_gb: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", index=True)
    error: Mapped[str | None] = mapped_column(String(1024))

    job: Mapped[BackupJob | None] = relationship()


class VeeamServer(Base):
    __tablename__ = "veeam_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    hostname: Mapped[str] = mapped_column(String(255))
    api_url: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=9419)
    username: Mapped[str | None] = mapped_column(String(128))
    password_enc: Mapped[str | None] = mapped_column(String(512))
    tls_verify: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class VeeamJob(Base):
    __tablename__ = "veeam_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    server_id: Mapped[int | None] = mapped_column(ForeignKey("veeam_servers.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    type: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="UNKNOWN", index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    transferred_gb: Mapped[float] = mapped_column(Float, default=0.0)
    backup_size_gb: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    server: Mapped[VeeamServer | None] = relationship()
