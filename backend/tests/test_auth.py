import os

os.environ.setdefault("SCHEDULER_ENABLED", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-with-at-least-32-bytes!!")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.permissions import ROLE_ADMIN, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.main import app
from app.models.auth import Permission, Role, User

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup_db() -> None:
    Base.metadata.create_all(engine)
    db = TestingSession()
    try:
        perms = []
        for name in ROLE_PERMISSIONS[ROLE_ADMIN]:
            p = Permission(name=name)
            db.add(p)
            perms.append(p)
        role = Role(name=ROLE_ADMIN, description="Admin")
        role.permissions = perms
        db.add(role)
        db.flush()
        db.add(User(username="admin", hashed_password=hash_password("admin"), role_id=role.id))
        db.commit()
    finally:
        db.close()


setup_db()
client = TestClient(app)


def test_login_wrong_password():
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "nope"})
    assert resp.status_code == 401


def test_login_and_me():
    resp = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"})
    assert resp.status_code == 200, resp.text
    tokens = resp.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert me.json()["role"]["name"] == ROLE_ADMIN


def test_refresh_flow():
    tokens = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"}).json()
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert resp.status_code == 200
    bad = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert bad.status_code == 401


def test_protected_route_requires_token():
    assert client.get("/api/v1/audit").status_code == 401
    assert client.get("/api/v1/dashboard/summary").status_code == 401
    tokens = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"}).json()
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/api/v1/audit", headers=h).status_code == 200
    assert client.get("/api/v1/dashboard/summary", headers=h).status_code == 200


def test_vm_action_requires_confirmation():
    tokens = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin"}).json()
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    resp = client.post("/api/v1/proxmox/vms/1/action", json={"action": "stop", "confirm": False}, headers=h)
    assert resp.status_code == 400
    assert "confirmation" in resp.json()["detail"]
