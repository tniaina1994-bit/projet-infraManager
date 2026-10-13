from fastapi import APIRouter

from app.api.v1 import alerts, audit, auth, backups, dashboard, infrastructures, proxmox, users, veeam, ws

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(infrastructures.router)
api_router.include_router(proxmox.router)
api_router.include_router(backups.router)
api_router.include_router(veeam.router)
api_router.include_router(alerts.router)
api_router.include_router(audit.router)
api_router.include_router(dashboard.router)
api_router.include_router(ws.router)
