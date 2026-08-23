"""WebSocket connection manager.

Tracks connected clients and broadcasts events safely: a single broken client
never prevents other clients from receiving messages, and disconnected clients
are removed automatically.
"""

from __future__ import annotations

import logging

from fastapi import WebSocket

from .events import Event

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages the set of connected WebSocket clients."""

    def __init__(self) -> None:
        self._active: set[WebSocket] = set()

    @property
    def client_count(self) -> int:
        return len(self._active)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active.add(websocket)
        logger.info("websocket client connected (%d active)", self.client_count)

    def disconnect(self, websocket: WebSocket) -> None:
        self._active.discard(websocket)
        logger.info("websocket client disconnected (%d active)", self.client_count)

    async def on_event(self, event: Event) -> None:
        """Event bus subscriber: broadcast the serialized event to all clients."""
        await self.broadcast(event.to_dict())

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            logger.warning("failed to send to client; removing it", exc_info=False)
            self._active.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        for websocket in list(self._active):
            await self.send_personal(websocket, message)
