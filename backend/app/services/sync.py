"""Periodic synchronisation Proxmox / Veeam -> PostgreSQL + alert generation (spec sections 22, 18)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.backup import VeeamServer
from app.models.infra import Container, Node, ProxmoxServer, Storage, VM
from app.models.ops import Alert, Setting
from app.services.proxmox import ProxmoxClient, ProxmoxError, client_from_server
from app.services.ws import hub


def get_threshold(db: Session, key: str, default: int) -> int:
    row = db.get(Setting, key)
    if row and row.value.isdigit():
        return int(row.value)
    return default


def raise_alert(
    db: Session,
    *,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
    source: str | None = None,
    resource: str | None = None,
) -> None:
    existing = db.scalar(
        select(Alert).where(
            Alert.alert_type == alert_type,
            Alert.resource == resource,
            Alert.status != "RESOLVED",
        )
    )
    if existing:
        return
    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        source=source,
        resource=resource,
    )
    db.add(alert)
    db.commit()
    hub.broadcast({"event": "alert", "title": title, "severity": severity, "type": alert_type})


def _pct(value: float) -> float:
    """Proxmox reports CPU as a 0..1 fraction."""
    return round(value * 100, 1) if 0 <= value <= 1 else round(value, 1)


def _pct_for(used: float, total: float) -> float:
    return round(used / total * 100, 1) if total else 0.0


def sync_proxmox(db: Session) -> dict:
    servers = db.scalars(select(ProxmoxServer).where(ProxmoxServer.enabled.is_(True))).all()
    summary = {"servers": len(servers), "nodes": 0, "vms": 0, "containers": 0, "storages": 0, "errors": []}

    for server in servers:
        try:
            client = client_from_server(server)
            resources = client.cluster_resources()
        except ProxmoxError as exc:
            summary["errors"].append(str(exc))
            raise_alert(
                db,
                alert_type="API_ERROR",
                severity="CRITICAL",
                title=f"Proxmox API error: {server.name}",
                description=str(exc),
                source="proxmox",
                resource=server.name,
            )
            continue

        node_ids: dict[str, int] = {}
        # Two passes: nodes first (cluster/resources does not guarantee node items come first)
        for item in resources:
            if item.get("type") == "node":
                node = _upsert_node(db, item)
                node_ids[_resource_name(item)] = node.id
                summary["nodes"] += 1

        for item in resources:
            ntype = item.get("type")
            if ntype == "qemu":
                summary["vms"] += _upsert_vm(db, node_ids, item)
            elif ntype == "lxc":
                summary["containers"] += _upsert_container(db, node_ids, item)
            elif ntype == "storage":
                summary["storages"] += _upsert_storage(db, node_ids, item)
                _check_storage_thresholds(db, item, server.name)

        for node_name, node_id in node_ids.items():
            try:
                _update_node_metrics(db, client, node_name, node_id)
            except ProxmoxError:
                pass

        server.last_sync_at = datetime.now(UTC)
        db.commit()

    hub.broadcast({"event": "sync", "system": "proxmox", **{k: v for k, v in summary.items() if k != "errors"}})
    return summary


def _resource_name(item: dict) -> str:
    # /cluster/resources: node entries have no "name" key — hostname lives in "node"
    return item.get("name") or item.get("node") or item.get("storage") or str(item.get("id", "")).split("/")[-1]


def _upsert_node(db: Session, item: dict) -> Node:
    name = _resource_name(item)
    node = db.scalar(select(Node).where(Node.name == name))
    if node is None:
        node = Node(name=name)
        db.add(node)
    node.status = item.get("status", "unknown")
    node.ip = item.get("ip") or node.ip
    node.cpu_usage = _pct(item.get("cpu", 0.0) or 0.0)
    maxmem = item.get("maxmem") or 0
    if maxmem:
        node.ram_usage = _pct_for(item.get("mem", 0) or 0, maxmem)
    maxdisk = item.get("maxdisk") or 0
    if maxdisk:
        node.disk_usage = _pct_for(item.get("disk", 0) or 0, maxdisk)
    node.uptime_seconds = int(item.get("uptime") or 0)
    db.commit()
    return node


def _node_by_id(db: Session, node_ids: dict[str, int], item: dict) -> Node | None:
    node_name = item.get("node")
    node_id = node_ids.get(node_name)
    if node_id is None:
        node = db.scalar(select(Node).where(Node.name == node_name)) if node_name else None
        return node
    return db.get(Node, node_id)


def _upsert_vm(db: Session, node_ids: dict[str, int], item: dict) -> int:
    node = _node_by_id(db, node_ids, item)
    if node is None:
        return 0
    vm = db.scalar(select(VM).where(VM.node_id == node.id, VM.vmid == item.get("vmid")))
    if vm is None:
        vm = VM(node_id=node.id, vmid=item.get("vmid", 0))
        db.add(vm)
    vm.name = item.get("name") or f"vm-{item.get('vmid')}"
    vm.status = item.get("status", "unknown")
    vm.cpu_usage = _pct(item.get("cpu", 0.0) or 0.0)
    vm.ram_mb = round((item.get("mem") or 0) / 1024 / 1024, 1)
    vm.disk_gb = round((item.get("disk") or 0) / 1024 / 1024 / 1024, 2)
    vm.uptime_seconds = int(item.get("uptime") or 0)
    db.commit()
    return 1


def _upsert_container(db: Session, node_ids: dict[str, int], item: dict) -> int:
    node = _node_by_id(db, node_ids, item)
    if node is None:
        return 0
    ct = db.scalar(select(Container).where(Container.node_id == node.id, Container.ctid == item.get("vmid")))
    if ct is None:
        ct = Container(node_id=node.id, ctid=item.get("vmid", 0))
        db.add(ct)
    ct.name = item.get("name") or f"ct-{item.get('vmid')}"
    ct.status = item.get("status", "unknown")
    ct.cpu_usage = _pct(item.get("cpu", 0.0) or 0.0)
    ct.ram_mb = round((item.get("mem") or 0) / 1024 / 1024, 1)
    ct.disk_gb = round((item.get("disk") or 0) / 1024 / 1024 / 1024, 2)
    ct.uptime_seconds = int(item.get("uptime") or 0)
    db.commit()
    return 1


def _storage_values(item: dict) -> tuple[float, float]:
    """cluster/resources exposes storage as used=disk, total=maxdisk (no free/total keys)."""
    total = item.get("total") or item.get("maxdisk") or 0
    used = item.get("used") or item.get("disk") or 0
    return total, used


def _upsert_storage(db: Session, node_ids: dict[str, int], item: dict) -> int:
    node = _node_by_id(db, node_ids, item)
    if node is None:
        return 0
    name = _resource_name(item)
    storage = db.scalar(select(Storage).where(Storage.node_id == node.id, Storage.name == name))
    if storage is None:
        storage = Storage(node_id=node.id, name=name)
        db.add(storage)
    storage.type = item.get("plugintype") or item.get("type")
    total, used = _storage_values(item)
    storage.total_gb = round(total / 1024**3, 2)
    storage.used_gb = round(used / 1024**3, 2)
    storage.free_gb = round((total - used) / 1024**3, 2)
    storage.status = item.get("status", "unknown")
    db.commit()
    return 1


def _check_storage_thresholds(db: Session, item: dict, server_name: str) -> None:
    total, used = _storage_values(item)
    if not total:
        return
    usage = used / total * 100
    name = f"{item.get('node')}/{_resource_name(item)}"
    full = get_threshold(db, "storage_full_threshold", settings.storage_full_threshold)
    critical = get_threshold(db, "storage_critical_threshold", settings.storage_critical_threshold)
    warning = get_threshold(db, "storage_warning_threshold", settings.storage_warning_threshold)
    if usage >= full:
        severity, alert_type = "CRITICAL", "REPOSITORY_FULL"
    elif usage >= critical:
        severity, alert_type = "CRITICAL", "HIGH_STORAGE"
    elif usage >= warning:
        severity, alert_type = "WARNING", "HIGH_STORAGE"
    else:
        return
    raise_alert(
        db,
        alert_type=alert_type,
        severity=severity,
        title=f"Storage {usage:.0f}% on {name}",
        description=f"Usage {usage:.1f}% exceeds threshold (warning={warning}%, critical={critical}%, full={full}%)",
        source=server_name,
        resource=name,
    )


def _update_node_metrics(db: Session, client: ProxmoxClient, node_name: str, node_id: int) -> None:
    node = db.get(Node, node_id)
    if node is None:
        return
    status = client.node_status(node_name)
    node.cpu_usage = _pct(status.get("cpu", 0.0) or 0.0)
    mem = status.get("memory") or {}
    node.ram_usage = _pct_for(mem.get("used", 0) or 0, mem.get("total", 0) or 0)
    rootfs = status.get("rootfs") or status.get("disk") or {}
    node.disk_usage = _pct_for(rootfs.get("used", 0) or 0, rootfs.get("total", 0) or 0)
    node.uptime_seconds = int(status.get("uptime") or 0)
    node.load = " ".join(str(x) for x in (status.get("loadavg") or []))
    node.kernel = status.get("kversion")
    node.version = status.get("pveversion")
    db.commit()


def sync_veeam(db: Session) -> dict:
    """Veeam REST API sync — only runs when a VeeamServer is registered and credentials work."""
    servers = db.scalars(select(VeeamServer).where(VeeamServer.enabled.is_(True))).all()
    if not servers:
        return {"servers": 0, "skipped": True}
    summary = {"servers": len(servers), "jobs": 0, "errors": []}
    for server in servers:
        try:
            jobs = _veeam_fetch_jobs(server)
        except Exception as exc:  # noqa: BLE001 — external API, keep the scheduler alive
            summary["errors"].append(str(exc))
            raise_alert(
                db,
                alert_type="API_ERROR",
                severity="CRITICAL",
                title=f"Veeam API error: {server.name}",
                description=str(exc),
                source="veeam",
                resource=server.name,
            )
            continue
        summary["jobs"] += len(jobs)
        server.last_sync_at = datetime.now(UTC)
        db.commit()
    return summary


def _veeam_fetch_jobs(server: VeeamServer) -> list[dict]:
    from app.services.veeam import client_from_veeam_server

    return client_from_veeam_server(server).jobs()
