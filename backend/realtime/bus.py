"""Application event bus.

Decouples event producers (the analytics service) from event consumers (the
WebSocket connection manager). Producers may run on worker threads (sync route
handlers), so ``publish`` is thread-safe and non-blocking; a single background
consumer dispatches events to subscribers on the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from .events import Event

logger = logging.getLogger(__name__)

Subscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    """Thread-safe publish / subscribe bus with an async dispatch loop."""

    def __init__(self) -> None:
        self._subscribers: list[Subscriber] = []
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._loop: asyncio.AbstractEventLoop | None = None

    def subscribe(self, handler: Subscriber) -> None:
        self._subscribers.append(handler)

    def unsubscribe(self, handler: Subscriber) -> None:
        self._subscribers = [h for h in self._subscribers if h is not handler]

    def publish(self, event: Event) -> None:
        """Enqueue an event for dispatch (safe to call from any thread)."""
        loop = self._loop
        if loop is None or loop.is_closed():
            logger.debug("event bus not running; dropping event %s", event.type.value)
            return
        loop.call_soon_threadsafe(self._queue.put_nowait, event)

    async def run(self) -> None:
        """Dispatch events to subscribers until cancelled."""
        self._loop = asyncio.get_running_loop()
        while True:
            event = await self._queue.get()
            for handler in list(self._subscribers):
                try:
                    await handler(event)
                except Exception:
                    logger.exception("event subscriber failed for %s", event.type.value)
