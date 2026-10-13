"""Veeam Backup REST API client (VBR 12+ : OAuth2 password grant, /api/v1/*)."""

from __future__ import annotations

import httpx

from app.core.crypto import decrypt
from app.models.backup import VeeamServer


class VeeamError(Exception):
    pass


class VeeamClient:
    def __init__(self, api_url: str, username: str, password: str, tls_verify: bool = True, timeout: float = 20.0):
        self.base = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.tls_verify = tls_verify
        self.timeout = timeout
        self._token: str | None = None

    def _login(self) -> str:
        try:
            resp = httpx.post(
                f"{self.base}/oauth2/token",
                data={"grant_type": "password", "username": self.username, "password": self.password},
                verify=self.tls_verify,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise VeeamError(f"Veeam unreachable: {exc}") from exc
        if resp.status_code >= 400:
            raise VeeamError(f"Veeam auth failed: {resp.status_code}")
        token = resp.json().get("access_token")
        if not token:
            raise VeeamError("Veeam auth: no access_token in response")
        return token

    def _get(self, path: str) -> dict | list:
        if self._token is None:
            self._token = self._login()
        try:
            resp = httpx.get(
                f"{self.base}{path}",
                headers={"Authorization": f"Bearer {self._token}"},
                verify=self.tls_verify,
                timeout=self.timeout,
            )
        except httpx.HTTPError as exc:
            raise VeeamError(f"Veeam unreachable: {exc}") from exc
        if resp.status_code == 401:
            self._token = self._login()
            resp = httpx.get(
                f"{self.base}{path}",
                headers={"Authorization": f"Bearer {self._token}"},
                verify=self.tls_verify,
                timeout=self.timeout,
            )
        if resp.status_code >= 400:
            raise VeeamError(f"Veeam GET {path} -> {resp.status_code}")
        return resp.json()

    def jobs(self) -> list[dict]:
        data = self._get("/api/v1/jobs")
        if isinstance(data, dict):
            return data.get("data", [])
        return list(data)

    def repositories(self) -> list[dict]:
        data = self._get("/api/v1/backupInfra/repositories")
        if isinstance(data, dict):
            return data.get("data", [])
        return list(data)


def client_from_veeam_server(server: VeeamServer) -> VeeamClient:
    return VeeamClient(
        api_url=server.api_url,
        username=server.username or "",
        password=decrypt(server.password_enc) if server.password_enc else "",
        tls_verify=server.tls_verify,
    )
