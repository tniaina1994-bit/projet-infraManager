"""In-memory WebSocket hub: backend pushes live status (spec section 23)."""

from __future__ import annotations

import asyncio
import contextlib

from fastapi import WebSocket


class Hub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._clients.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._clients.discard(ws)

    async def _send(self, event: dict) -> None:
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_json(event)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)

    def broadcast(self, event: dict) -> None:
        """Thread-safe: scheduler jobs run outside the event loop."""
        if not self._clients:
            return
        loop = self._loop
        if loop is None or loop.is_closed():
            return
        try:
            running = asyncio.get_running_loop()
        except RuntimeError:
            running = None
        if running is loop:
            asyncio.create_task(self._send(event))
        else:
            with contextlib.suppress(RuntimeError):
                asyncio.run_coroutine_threadsafe(self._send(event), loop)


hub = Hub()
