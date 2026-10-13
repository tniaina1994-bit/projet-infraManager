from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class Environment(str, Enum):
    Production = "Production"
    Staging = "Staging"
    Development = "Development"
    Lab = "Lab"


class BackupStatus(str, Enum):
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class RoleName(str, Enum):
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RoleOut(ORMModel):
    id: int
    name: str
    description: str | None = None


class UserOut(ORMModel):
    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    is_active: bool
    role: RoleOut
    created_at: datetime


class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None
    role: RoleName = RoleName.VIEWER


class UserUpdate(BaseModel):
    email: str | None = None
    full_name: str | None = None
    is_active: bool | None = None
    role: RoleName | None = None
    password: str | None = None


class InfrastructureCreate(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    environment: Environment = Environment.Production
    provider: str | None = None
    api_endpoint: str | None = None
    status: str = "unknown"


class InfrastructureUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    environment: Environment | None = None
    provider: str | None = None
    api_endpoint: str | None = None
    status: str | None = None


class InfrastructureOut(ORMModel):
    id: int
    name: str
    description: str | None
    location: str | None
    environment: str
    status: str
    provider: str | None
    api_endpoint: str | None
    created_at: datetime
    updated_at: datetime


class DatacenterOut(ORMModel):
    id: int
    infrastructure_id: int
    name: str
    status: str


class NodeOut(ORMModel):
    id: int
    name: str
    status: str
    ip: str | None
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    uptime_seconds: int
    kernel: str | None
    version: str | None
    load: str | None
    updated_at: datetime


class VMOut(ORMModel):
    id: int
    node_id: int
    node_name: str | None = None
    vmid: int
    name: str
    status: str
    cpu_usage: float
    ram_mb: float
    disk_gb: float
    ip: str | None
    uptime_seconds: int


class ContainerOut(ORMModel):
    id: int
    node_id: int
    node_name: str | None = None
    ctid: int
    name: str
    status: str
    cpu_usage: float
    ram_mb: float
    disk_gb: float
    ip: str | None
    uptime_seconds: int


class StorageOut(ORMModel):
    id: int
    node_id: int
    name: str
    type: str | None
    total_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    status: str


class ProxmoxServerCreate(BaseModel):
    name: str
    host: str
    api_url: str
    port: int = 8006
    token_id: str
    token_secret: str
    tls_verify: bool = True


class ProxmoxServerOut(ORMModel):
    id: int
    name: str
    host: str
    api_url: str
    port: int
    auth_method: str
    token_id: str
    tls_verify: bool
    enabled: bool
    last_sync_at: datetime | None
    created_at: datetime


class VMActionRequest(BaseModel):
    """Critical actions (stop/shutdown/reboot) require confirm=true — spec section 9."""

    action: str  # start | stop | shutdown | reboot
    confirm: bool = False


class BackupJobOut(ORMModel):
    id: int
    name: str
    source: str | None
    target: str | None
    schedule: str | None
    retention: str | None
    backup_type: str | None
    environment: str | None
    server: str | None
    last_run_at: datetime | None
    next_run_at: datetime | None
    duration_seconds: int
    size_gb: float
    status: str


class BackupHistoryOut(ORMModel):
    id: int
    job_name: str | None
    server: str | None
    vm: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int
    backup_size_gb: float
    transferred_gb: float
    status: str
    error: str | None


class BackupRepositoryOut(ORMModel):
    id: int
    name: str
    type: str | None
    total_capacity_gb: float
    used_gb: float
    free_gb: float
    usage_percent: float
    status: str
    last_backup_at: datetime | None


class VeeamServerCreate(BaseModel):
    name: str
    hostname: str
    api_url: str
    port: int = 9419
    username: str | None = None
    password: str | None = None
    tls_verify: bool = True


class VeeamServerOut(ORMModel):
    id: int
    name: str
    hostname: str
    api_url: str
    port: int
    username: str | None
    tls_verify: bool
    enabled: bool
    last_sync_at: datetime | None


class VeeamJobOut(ORMModel):
    id: int
    name: str
    type: str | None
    status: str
    last_run_at: datetime | None
    next_run_at: datetime | None
    duration_seconds: int
    transferred_gb: float
    backup_size_gb: float


class AlertOut(ORMModel):
    id: int
    alert_type: str
    severity: str
    title: str
    description: str | None
    source: str | None
    resource: str | None
    status: str
    timestamp: datetime


class AlertUpdate(BaseModel):
    status: str  # NEW | ACK | RESOLVED


class AuditLogOut(ORMModel):
    id: int
    username: str
    action: str
    resource: str | None
    resource_id: str | None
    ip_address: str | None
    result: str
    timestamp: datetime


class NotificationChannelCreate(BaseModel):
    type: str  # email | telegram | discord | webhook
    name: str
    config: dict = {}
    enabled: bool = True


class NotificationChannelOut(ORMModel):
    id: int
    type: str
    name: str
    config: dict
    enabled: bool


class DashboardSummary(BaseModel):
    datacenters: int
    nodes: int
    vms: int
    containers: int
    veeam_servers: int
    backup_repositories: int
    nodes_online: int
    nodes_offline: int
    vms_running: int
    vms_stopped: int
    storage_warnings: int
    backup_failures: int
    backup_warnings: int
    last_successful_backup: datetime | None
    running_backups: int
    recent_activity: list[dict]
