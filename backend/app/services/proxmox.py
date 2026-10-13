"""Proxmox VE API client — the only place that talks to Proxmox (credentials stay server-side)."""

from __future__ import annotations

import httpx

from app.core.crypto import decrypt
from app.models.infra import ProxmoxServer

VM_ACTIONS = {"start", "stop", "shutdown", "reboot"}
CRITICAL_ACTIONS = {"stop", "shutdown", "reboot"}  # require user confirmation (spec section 9)


class ProxmoxError(Exception):
    pass


class ProxmoxClient:
    def __init__(self, api_url: str, token_id: str, token_secret: str, tls_verify: bool = True, timeout: float = 15.0):
        self.base = api_url.rstrip("/")
        self.headers = {"Authorization": f"PVEAPIToken={token_id}={token_secret}"}
        self.tls_verify = tls_verify
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs) -> dict:
        url = f"{self.base}/api2/json{path}"
        try:
            resp = httpx.request(
                method,
                url,
                headers=self.headers,
                verify=self.tls_verify,
                timeout=self.timeout,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise ProxmoxError(f"Proxmox unreachable: {exc}") from exc
        if resp.status_code >= 400:
            detail = ""
            try:
                detail = resp.json().get("message", "")
            except ValueError:
                detail = resp.text[:200]
            raise ProxmoxError(f"Proxmox {method} {path} -> {resp.status_code}: {detail}")
        data = resp.json().get("data")
        return data if data is not None else {}

    def version(self) -> dict:
        return self._request("GET", "/version")

    def cluster_resources(self) -> list[dict]:
        return self._request("GET", "/cluster/resources") or []

    def node_status(self, node: str) -> dict:
        return self._request("GET", f"/nodes/{node}/status")

    def node_storage(self, node: str) -> list[dict]:
        return self._request("GET", f"/nodes/{node}/storage") or []

    def vm_status(self, node: str, vmid: int) -> dict:
        return self._request("GET", f"/nodes/{node}/qemu/{vmid}/status/current")

    def set_vm_state(self, node: str, vmid: int, action: str) -> dict:
        if action not in VM_ACTIONS:
            raise ProxmoxError(f"Unsupported action: {action}")
        return self._request("POST", f"/nodes/{node}/qemu/{vmid}/status/{action}")

    def set_ct_state(self, node: str, ctid: int, action: str) -> dict:
        if action not in VM_ACTIONS:
            raise ProxmoxError(f"Unsupported action: {action}")
        return self._request("POST", f"/nodes/{node}/lxc/{ctid}/status/{action}")


def client_from_server(server: ProxmoxServer) -> ProxmoxClient:
    return ProxmoxClient(
        api_url=server.api_url,
        token_id=server.token_id,
        token_secret=decrypt(server.token_secret_enc),
        tls_verify=server.tls_verify,
    )
