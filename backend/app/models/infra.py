from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Infrastructure(Base):
    __tablename__ = "infrastructures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    description: Mapped[str | None] = mapped_column(String(512))
    location: Mapped[str | None] = mapped_column(String(128))
    environment: Mapped[str] = mapped_column(String(32), default="Production")  # Production/Staging/Development/Lab
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    provider: Mapped[str | None] = mapped_column(String(64))
    api_endpoint: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Datacenter(Base):
    __tablename__ = "datacenters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    infrastructure_id: Mapped[int] = mapped_column(ForeignKey("infrastructures.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="unknown")

    clusters: Mapped[list[Cluster]] = relationship(back_populates="datacenter", cascade="all, delete-orphan")


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    datacenter_id: Mapped[int] = mapped_column(ForeignKey("datacenters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="unknown")

    datacenter: Mapped[Datacenter] = relationship(back_populates="clusters")
    nodes: Mapped[list[Node]] = relationship(back_populates="cluster", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    ip: Mapped[str | None] = mapped_column(String(64))
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0)
    ram_usage: Mapped[float] = mapped_column(Float, default=0.0)
    disk_usage: Mapped[float] = mapped_column(Float, default=0.0)
    uptime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    kernel: Mapped[str | None] = mapped_column(String(128))
    version: Mapped[str | None] = mapped_column(String(64))
    load: Mapped[str | None] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    cluster: Mapped[Cluster | None] = relationship(back_populates="nodes")
    vms: Mapped[list[VM]] = relationship(back_populates="node", cascade="all, delete-orphan")
    containers: Mapped[list[Container]] = relationship(back_populates="node", cascade="all, delete-orphan")
    storages: Mapped[list[Storage]] = relationship(back_populates="node", cascade="all, delete-orphan")


class VM(Base):
    __tablename__ = "vms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    vmid: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0)
    ram_mb: Mapped[float] = mapped_column(Float, default=0.0)
    disk_gb: Mapped[float] = mapped_column(Float, default=0.0)
    ip: Mapped[str | None] = mapped_column(String(64))
    uptime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    node: Mapped[Node] = relationship(back_populates="vms")

    @property
    def node_name(self) -> str | None:
        return self.node.name if self.node else None


class Container(Base):
    __tablename__ = "containers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    # "ctid" is a reserved system column name in PostgreSQL — DB column renamed, API field stays "ctid".
    ctid: Mapped[int] = mapped_column("ctid_value", Integer)
    name: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0)
    ram_mb: Mapped[float] = mapped_column(Float, default=0.0)
    disk_gb: Mapped[float] = mapped_column(Float, default=0.0)
    ip: Mapped[str | None] = mapped_column(String(64))
    uptime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    node: Mapped[Node] = relationship(back_populates="containers")

    @property
    def node_name(self) -> str | None:
        return self.node.name if self.node else None


class Storage(Base):
    __tablename__ = "storages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[str | None] = mapped_column(String(64))
    total_gb: Mapped[float] = mapped_column(Float, default=0.0)
    used_gb: Mapped[float] = mapped_column(Float, default=0.0)
    free_gb: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    node: Mapped[Node] = relationship(back_populates="storages")

    @property
    def usage_percent(self) -> float:
        if not self.total_gb:
            return 0.0
        return round(self.used_gb / self.total_gb * 100, 1)


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    datacenter_id: Mapped[int] = mapped_column(ForeignKey("datacenters.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128))
    cidr: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="unknown")


class ProxmoxServer(Base):
    __tablename__ = "proxmox_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    host: Mapped[str] = mapped_column(String(255))
    api_url: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer, default=8006)
    auth_method: Mapped[str] = mapped_column(String(32), default="api_token")
    token_id: Mapped[str] = mapped_column(String(255))
    token_secret_enc: Mapped[str] = mapped_column(String(512))
    tls_verify: Mapped[bool] = mapped_column(Boolean, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
