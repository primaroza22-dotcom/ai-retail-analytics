"""Tests for the real-time subsystem (Sprint 10).

Covers the event envelope, the event bus, the WebSocket connection manager, and
an end-to-end flow (WebSocket client receives a zone_enter event published via
the REST API).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.database import Base
from backend.realtime import ConnectionManager, Event, EventBus, EventType

ZONE = {
    "id": "counter",
    "name": "Counter",
    "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as c:
        yield c


# --- Event envelope ---


def test_event_envelope_serialization() -> None:
    event = Event(EventType.ZONE_ENTER, 123.0, {"zone_id": "z", "track_id": 7})
    assert event.to_dict() == {
        "type": "zone_enter",
        "version": 1,
        "timestamp": 123.0,
        "data": {"zone_id": "z", "track_id": 7},
    }


# --- Event bus ---


def test_event_bus_dispatches_to_subscriber() -> None:
    async def scenario() -> None:
        bus = EventBus()
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe(handler)
        task = asyncio.create_task(bus.run())
        await asyncio.sleep(0)
        bus.publish(Event(EventType.DWELL_COMPLETED, 1.0, {"duration": 30.0}))
        await asyncio.sleep(0.01)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(received) == 1
        assert received[0].type == EventType.DWELL_COMPLETED

    asyncio.run(scenario())


def test_event_bus_subscriber_failure_does_not_break_bus() -> None:
    async def scenario() -> None:
        bus = EventBus()
        received: list[Event] = []

        async def bad_handler(event: Event) -> None:
            raise RuntimeError("boom")

        async def good_handler(event: Event) -> None:
            received.append(event)

        bus.subscribe(bad_handler)
        bus.subscribe(good_handler)
        task = asyncio.create_task(bus.run())
        await asyncio.sleep(0)
        bus.publish(Event(EventType.ZONE_EXIT, 2.0, {}))
        await asyncio.sleep(0.01)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        assert len(received) == 1

    asyncio.run(scenario())


# --- Connection manager ---


def test_connection_manager_connect_disconnect() -> None:
    async def scenario() -> None:
        manager = ConnectionManager()

        class FakeWS:
            async def accept(self) -> None:
                pass

            async def send_json(self, message: dict) -> None:
                pass

        ws = FakeWS()
        await manager.connect(ws)
        assert manager.client_count == 1
        manager.disconnect(ws)
        assert manager.client_count == 0

    asyncio.run(scenario())


def test_broadcast_skips_broken_client() -> None:
    async def scenario() -> None:
        manager = ConnectionManager()

        class FakeWS:
            def __init__(self, fail: bool = False) -> None:
                self.sent: list[dict] = []
                self.fail = fail

            async def accept(self) -> None:
                pass

            async def send_json(self, message: dict) -> None:
                if self.fail:
                    raise RuntimeError("broken client")
                self.sent.append(message)

        good = FakeWS()
        broken = FakeWS(fail=True)
        await manager.connect(good)
        await manager.connect(broken)
        assert manager.client_count == 2

        await manager.broadcast({"type": "heartbeat"})

        assert good.sent == [{"type": "heartbeat"}]
        assert broken.sent == []
        assert manager.client_count == 1

    asyncio.run(scenario())


# --- Integration ---


def test_websocket_connection_confirmation(client: TestClient) -> None:
    with client.websocket_connect("/ws/events") as ws:
        message = ws.receive_json()
        assert message["type"] == "connection"
        assert message["data"]["status"] == "connected"


def test_websocket_receives_zone_enter_event(client: TestClient) -> None:
    client.post("/zones", json=ZONE)
    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection"

        client.post(
            "/events",
            json=[{"track_id": 1, "zone_id": "counter", "event_type": "enter", "timestamp": 10.0}],
        )

        event = ws.receive_json()
        assert event["type"] == "zone_enter"
        assert event["data"]["track_id"] == 1
        assert event["data"]["zone_id"] == "counter"


def test_websocket_receives_dwell_completed_event(client: TestClient) -> None:
    client.post("/zones", json=ZONE)
    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection"

        client.post(
            "/dwell-sessions",
            json=[{"track_id": 5, "zone_id": "counter", "enter_time": 10.0, "exit_time": 40.0}],
        )

        event = ws.receive_json()
        assert event["type"] == "dwell_completed"
        assert event["data"]["duration"] == 30.0


def test_websocket_receives_dwell_started_event(client: TestClient) -> None:
    client.post("/zones", json=ZONE)
    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection"

        client.post(
            "/dwell-sessions",
            json=[{"track_id": 9, "zone_id": "counter", "enter_time": 100.0}],
        )

        event = ws.receive_json()
        assert event["type"] == "dwell_started"
        assert event["data"]["track_id"] == 9
