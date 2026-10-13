from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import VEEAM_READ, VEEAM_WRITE
from app.models.auth import User
from app.models.backup import VeeamJob, VeeamServer
from app.schemas import VeeamJobOut, VeeamServerCreate, VeeamServerOut
from app.services.audit import log_action

router = APIRouter(prefix="/veeam", tags=["veeam"])


@router.get("/servers", response_model=list[VeeamServerOut])
def list_servers(db: Session = Depends(get_db), _: User = Depends(require_permission(VEEAM_READ))):
    return db.scalars(select(VeeamServer).order_by(VeeamServer.id)).all()


@router.post("/servers", response_model=VeeamServerOut, status_code=status.HTTP_201_CREATED)
def add_server(
    payload: VeeamServerCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(VEEAM_WRITE)),
):
    from app.core.crypto import encrypt

    if db.scalar(select(VeeamServer).where(VeeamServer.name == payload.name)):
        raise HTTPException(status_code=409, detail="Server already exists")
    data = payload.model_dump()
    password = data.pop("password")
    server = VeeamServer(
        **data,
        password_enc=encrypt(password) if password else None,
    )
    db.add(server)
    db.commit()
    db.refresh(server)
    log_action(
        db,
        username=user.username,
        action="add_veeam_server",
        resource="veeam_server",
        resource_id=server.id,
        ip_address=request.client.host if request.client else None,
    )
    return server


@router.get("/jobs", response_model=list[VeeamJobOut])
def list_jobs(db: Session = Depends(get_db), _: User = Depends(require_permission(VEEAM_READ))):
    return db.scalars(select(VeeamJob).order_by(VeeamJob.name)).all()
