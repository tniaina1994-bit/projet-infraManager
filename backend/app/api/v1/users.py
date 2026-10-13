from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_permission
from app.core.permissions import ROLE_ADMIN, USERS_READ, USERS_WRITE
from app.core.security import hash_password
from app.models.auth import Role, User
from app.schemas import RoleName, UserCreate, UserOut, UserUpdate
from app.services.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USERS_READ)),
):
    return db.scalars(select(User).order_by(User.id)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(USERS_WRITE)),
):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="Username already exists")
    role = db.scalar(select(Role).where(Role.name == payload.role.value))
    if role is None:
        raise HTTPException(status_code=422, detail="Unknown role")
    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role_id=role.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(
        db,
        username=current.username,
        action="create_user",
        resource="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(USERS_WRITE)),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.role is not None:
        role = db.scalar(select(Role).where(Role.name == payload.role.value))
        if role is None:
            raise HTTPException(status_code=422, detail="Unknown role")
        user.role_id = role.id
    if payload.email is not None:
        user.email = payload.email
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.is_active is not None:
        if user.id == current.id and not payload.is_active:
            raise HTTPException(status_code=422, detail="Cannot disable yourself")
        user.is_active = payload.is_active
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    log_action(
        db,
        username=current.username,
        action="update_user",
        resource="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(require_permission(USERS_WRITE)),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current.id:
        raise HTTPException(status_code=422, detail="Cannot delete yourself")
    if user.role and user.role.name == ROLE_ADMIN:
        admins = db.scalars(select(User).join(Role).where(Role.name == ROLE_ADMIN)).all()
        if len(admins) <= 1:
            raise HTTPException(status_code=422, detail="Cannot delete the last admin")
    log_action(
        db,
        username=current.username,
        action="delete_user",
        resource="user",
        resource_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.delete(user)
    db.commit()


@router.get("/roles", response_model=list[RoleName])
def list_roles(db: Session = Depends(get_db), _: User = Depends(require_permission(USERS_READ))):
    return [r.name for r in db.scalars(select(Role).order_by(Role.id)).all()]
