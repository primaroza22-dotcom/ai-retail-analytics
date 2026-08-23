"""WebSocket connection manager.

Tracks connected clients, their camera subscriptions, and broadcasts events
safely: a single broken client never prevents other clients from receiving
messages, and disconnected clients are removed automatically.
"""

from __future__ import annotations

import logging

from fastapi import WebSocket

from .events import Event

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages connected WebSocket clients and per-client camera subscriptions."""

    def __init__(self) -> None:
        # websocket -> subscription (None = all cameras, set[str] = only those).
        self._active: dict[WebSocket, set[str] | None] = {}

    @property
    def client_count(self) -> int:
        return len(self._active)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active[websocket] = None
        logger.info("websocket client connected (%d active)", self.client_count)

    def disconnect(self, websocket: WebSocket) -> None:
        self._active.pop(websocket, None)
        logger.info("websocket client disconnected (%d active)", self.client_count)

    def subscribe(self, websocket: WebSocket, camera_ids: list[str] | None) -> None:
        if not camera_ids:
            self._active[websocket] = None  # all cameras
        else:
            self._active[websocket] = set(camera_ids)

    def unsubscribe(self, websocket: WebSocket, camera_ids: list[str]) -> None:
        current = self._active.get(websocket)
        if current is None:
            return  # subscribed to all; nothing to remove
        for camera_id in camera_ids:
            current.discard(camera_id)
        if not current:
            self._active[websocket] = None

    def _matches(self, subscription: set[str] | None, camera_id: str | None) -> bool:
        if subscription is None:
            return True
        return camera_id is not None and camera_id in subscription

    async def on_event(self, event: Event) -> None:
        """Event bus subscriber: broadcast the serialized event to subscribed clients."""
        message = event.to_dict()
        camera_id = event.camera_id
        for websocket, subscription in list(self._active.items()):
            if self._matches(subscription, camera_id):
                await self.send_personal(websocket, message)

    async def send_personal(self, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            logger.warning("failed to send to client; removing it", exc_info=False)
            self._active.pop(websocket, None)

    async def broadcast(self, message: dict) -> None:
        """Broadcast to every client regardless of camera subscription."""
        for websocket in list(self._active):
            await self.send_personal(websocket, message)
