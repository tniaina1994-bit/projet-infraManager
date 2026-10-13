"""Idempotent seed: roles, permissions, admin user, thresholds, Proxmox server from env.

Run: python -m app.seed
"""

from __future__ import annotations

import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.crypto import encrypt
from app.core.database import SessionLocal
from app.core.permissions import ALL_PERMISSIONS, ROLE_ADMIN, ROLE_OPERATOR, ROLE_PERMISSIONS, ROLE_VIEWER
from app.core.security import hash_password
from app.models.auth import Permission, Role, User
from app.models.infra import ProxmoxServer
from app.models.ops import Setting


def seed() -> None:
    db = SessionLocal()
    try:
        permissions: dict[str, Permission] = {}
        for name in ALL_PERMISSIONS:
            perm = db.scalar(select(Permission).where(Permission.name == name))
            if perm is None:
                perm = Permission(name=name)
                db.add(perm)
                db.flush()
            permissions[name] = perm

        for role_name in (ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER):
            role = db.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                role = Role(name=role_name, description=role_name.title())
                db.add(role)
                db.flush()
            role.permissions = [permissions[p] for p in ROLE_PERMISSIONS[role_name]]

        admin = db.scalar(select(User).where(User.username == settings.admin_username))
        if admin is None:
            admin_role = db.scalar(select(Role).where(Role.name == ROLE_ADMIN))
            admin = User(
                username=settings.admin_username,
                full_name="Administrator",
                hashed_password=hash_password(settings.admin_password),
                role_id=admin_role.id,
            )
            db.add(admin)
            print(f"created admin user '{settings.admin_username}'")
        else:
            print(f"admin user '{settings.admin_username}' already exists")

        for key, value in {
            "storage_warning_threshold": settings.storage_warning_threshold,
            "storage_critical_threshold": settings.storage_critical_threshold,
            "storage_full_threshold": settings.storage_full_threshold,
        }.items():
            if db.get(Setting, key) is None:
                db.add(Setting(key=key, value=str(value)))

        if settings.proxmox_url and settings.proxmox_token_id and settings.proxmox_token_secret:
            existing = db.scalar(select(ProxmoxServer).where(ProxmoxServer.name == "primary"))
            if existing is None:
                db.add(
                    ProxmoxServer(
                        name="primary",
                        host=settings.proxmox_url.split("//")[-1].split("/")[0],
                        api_url=settings.proxmox_url,
                        port=8006,
                        token_id=settings.proxmox_token_id,
                        token_secret_enc=encrypt(settings.proxmox_token_secret),
                        tls_verify=settings.proxmox_tls_verify,
                    )
                )
                print(f"registered Proxmox server {settings.proxmox_url}")

        db.commit()
        print("seed complete")
    finally:
        db.close()


if __name__ == "__main__":
    try:
        seed()
    except Exception as exc:  # noqa: BLE001
        print(f"seed failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
