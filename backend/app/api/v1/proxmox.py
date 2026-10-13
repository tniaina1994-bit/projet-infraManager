from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import PROXMOX_READ, PROXMOX_WRITE
from app.models.auth import User
from app.models.infra import Container, Node, ProxmoxServer, Storage, VM
from app.schemas import (
    ContainerOut,
    NodeOut,
    ProxmoxServerCreate,
    ProxmoxServerOut,
    StorageOut,
    VMActionRequest,
    VMOut,
)
from app.services.audit import log_action
from app.services.proxmox import CRITICAL_ACTIONS, ProxmoxError, client_from_server
from app.services.sync import sync_proxmox

router = APIRouter(prefix="/proxmox", tags=["proxmox"])


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/servers", response_model=list[ProxmoxServerOut])
def list_servers(db: Session = Depends(get_db), _: User = Depends(require_permission(PROXMOX_READ))):
    return db.scalars(select(ProxmoxServer).order_by(ProxmoxServer.id)).all()


@router.post("/servers", response_model=ProxmoxServerOut, status_code=status.HTTP_201_CREATED)
def add_server(
    payload: ProxmoxServerCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PROXMOX_WRITE)),
):
    from app.core.crypto import encrypt

    if db.scalar(select(ProxmoxServer).where(ProxmoxServer.name == payload.name)):
        raise HTTPException(status_code=409, detail="Server already exists")
    data = payload.model_dump()
    secret = data.pop("token_secret")
    server = ProxmoxServer(**data, token_secret_enc=encrypt(secret))
    db.add(server)
    db.commit()
    db.refresh(server)
    log_action(
        db,
        username=user.username,
        action="add_proxmox_server",
        resource="proxmox_server",
        resource_id=server.id,
        ip_address=_client_ip(request),
    )
    return server


@router.delete("/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_server(
    server_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PROXMOX_WRITE)),
):
    server = db.get(ProxmoxServer, server_id)
    if server is None:
        raise HTTPException(status_code=404, detail="Server not found")
    log_action(
        db,
        username=user.username,
        action="delete_proxmox_server",
        resource="proxmox_server",
        resource_id=server.id,
        ip_address=_client_ip(request),
    )
    db.delete(server)
    db.commit()


@router.get("/nodes", response_model=list[NodeOut])
def list_nodes(db: Session = Depends(get_db), _: User = Depends(require_permission(PROXMOX_READ))):
    return db.scalars(select(Node).order_by(Node.name)).all()


@router.get("/vms", response_model=list[VMOut])
def list_vms(db: Session = Depends(get_db), _: User = Depends(require_permission(PROXMOX_READ))):
    return db.scalars(select(VM).order_by(VM.vmid)).all()


@router.get("/containers", response_model=list[ContainerOut])
def list_containers(db: Session = Depends(get_db), _: User = Depends(require_permission(PROXMOX_READ))):
    return db.scalars(select(Container).order_by(Container.ctid)).all()


@router.get("/storage", response_model=list[StorageOut])
def list_storage(db: Session = Depends(get_db), _: User = Depends(require_permission(PROXMOX_READ))):
    return db.scalars(select(Storage).order_by(Storage.name)).all()


def _run_action(db: Session, user: User, request: Request, kind: str, obj_id: int, payload: VMActionRequest):
    if payload.action not in {"start", "stop", "shutdown", "reboot"}:
        raise HTTPException(status_code=422, detail="Unsupported action")
    if payload.action in CRITICAL_ACTIONS and not payload.confirm:
        raise HTTPException(
            status_code=400,
            detail=f"Critical action '{payload.action}' requires confirmation",
        )
    node_name, target_id = None, None
    if kind == "vm":
        vm = db.get(VM, obj_id)
        if vm is None:
            raise HTTPException(status_code=404, detail="VM not found")
        node_name, target_id = vm.node.name, vm.vmid
        label = f"VM {vm.vmid}"
    else:
        ct = db.get(Container, obj_id)
        if ct is None:
            raise HTTPException(status_code=404, detail="Container not found")
        node_name, target_id = ct.node.name, ct.ctid
        label = f"CT {ct.ctid}"

    server = db.scalar(select(ProxmoxServer).where(ProxmoxServer.enabled.is_(True)).limit(1))
    if server is None:
        raise HTTPException(status_code=400, detail="No Proxmox server configured")
    client = client_from_server(server)
    try:
        if kind == "vm":
            client.set_vm_state(node_name, target_id, payload.action)
        else:
            client.set_ct_state(node_name, target_id, payload.action)
    except ProxmoxError as exc:
        log_action(
            db,
            username=user.username,
            action=f"{payload.action}_{kind}",
            resource=kind,
            resource_id=target_id,
            ip_address=_client_ip(request),
            result="FAILURE",
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    log_action(
        db,
        username=user.username,
        action=f"{payload.action}_{kind}",
        resource=kind,
        resource_id=target_id,
        ip_address=_client_ip(request),
    )
    return {"ok": True, "detail": f"{payload.action} sent to {label}"}


@router.post("/vms/{vm_id}/action")
def vm_action(
    vm_id: int,
    payload: VMActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PROXMOX_WRITE)),
):
    return _run_action(db, user, request, "vm", vm_id, payload)


@router.post("/containers/{ct_id}/action")
def container_action(
    ct_id: int,
    payload: VMActionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PROXMOX_WRITE)),
):
    return _run_action(db, user, request, "ct", ct_id, payload)


@router.post("/sync")
def trigger_sync(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(PROXMOX_WRITE)),
):
    summary = sync_proxmox(db)
    log_action(
        db,
        username=user.username,
        action="proxmox_sync",
        resource="proxmox",
        ip_address=_client_ip(request),
    )
    return summary
