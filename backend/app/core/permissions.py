"""RBAC permission strings and role definitions — taken verbatim from InfraManager.md section 4."""

INFRASTRUCTURE_READ = "infrastructure.read"
INFRASTRUCTURE_WRITE = "infrastructure.write"
PROXMOX_READ = "proxmox.read"
PROXMOX_WRITE = "proxmox.write"
BACKUP_READ = "backup.read"
BACKUP_WRITE = "backup.write"
VEEAM_READ = "veeam.read"
VEEAM_WRITE = "veeam.write"
USERS_READ = "users.read"
USERS_WRITE = "users.write"
AUDIT_READ = "audit.read"

ALL_PERMISSIONS = [
    INFRASTRUCTURE_READ,
    INFRASTRUCTURE_WRITE,
    PROXMOX_READ,
    PROXMOX_WRITE,
    BACKUP_READ,
    BACKUP_WRITE,
    VEEAM_READ,
    VEEAM_WRITE,
    USERS_READ,
    USERS_WRITE,
    AUDIT_READ,
]

ROLE_ADMIN = "ADMIN"
ROLE_OPERATOR = "OPERATOR"
ROLE_VIEWER = "VIEWER"

ROLE_PERMISSIONS: dict[str, list[str]] = {
    ROLE_ADMIN: list(ALL_PERMISSIONS),
    ROLE_OPERATOR: [
        INFRASTRUCTURE_READ,
        PROXMOX_READ,
        PROXMOX_WRITE,
        BACKUP_READ,
        BACKUP_WRITE,
        VEEAM_READ,
        VEEAM_WRITE,
        AUDIT_READ,
    ],
    ROLE_VIEWER: [
        INFRASTRUCTURE_READ,
        PROXMOX_READ,
        BACKUP_READ,
        VEEAM_READ,
    ],
}
