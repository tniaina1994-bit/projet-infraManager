from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import INFRASTRUCTURE_READ, INFRASTRUCTURE_WRITE
from app.models.auth import User
from app.models.infra import Datacenter, Infrastructure
from app.schemas import DatacenterOut, InfrastructureCreate, InfrastructureOut, InfrastructureUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/infrastructures", tags=["infrastructures"])


@router.get("", response_model=list[InfrastructureOut])
def list_infrastructures(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(INFRASTRUCTURE_READ)),
):
    return db.scalars(select(Infrastructure).order_by(Infrastructure.id)).all()


@router.post("", response_model=InfrastructureOut, status_code=status.HTTP_201_CREATED)
def create_infrastructure(
    payload: InfrastructureCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(INFRASTRUCTURE_WRITE)),
):
    if db.scalar(select(Infrastructure).where(Infrastructure.name == payload.name)):
        raise HTTPException(status_code=409, detail="Infrastructure already exists")
    infra = Infrastructure(**payload.model_dump())
    db.add(infra)
    db.commit()
    db.refresh(infra)
    log_action(
        db,
        username=user.username,
        action="create_infrastructure",
        resource="infrastructure",
        resource_id=infra.id,
        ip_address=request.client.host if request.client else None,
    )
    return infra


@router.patch("/{infra_id}", response_model=InfrastructureOut)
def update_infrastructure(
    infra_id: int,
    payload: InfrastructureUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(INFRASTRUCTURE_WRITE)),
):
    infra = db.get(Infrastructure, infra_id)
    if infra is None:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(infra, key, value.value if hasattr(value, "value") else value)
    db.commit()
    db.refresh(infra)
    log_action(
        db,
        username=user.username,
        action="update_infrastructure",
        resource="infrastructure",
        resource_id=infra.id,
        ip_address=request.client.host if request.client else None,
    )
    return infra


@router.delete("/{infra_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_infrastructure(
    infra_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(INFRASTRUCTURE_WRITE)),
):
    infra = db.get(Infrastructure, infra_id)
    if infra is None:
        raise HTTPException(status_code=404, detail="Infrastructure not found")
    log_action(
        db,
        username=user.username,
        action="delete_infrastructure",
        resource="infrastructure",
        resource_id=infra.id,
        ip_address=request.client.host if request.client else None,
    )
    db.delete(infra)
    db.commit()


@router.get("/datacenters", response_model=list[DatacenterOut])
def list_datacenters(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(INFRASTRUCTURE_READ)),
):
    return db.scalars(select(Datacenter).order_by(Datacenter.id)).all()
