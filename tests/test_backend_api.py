"""API tests for the FastAPI backend (Sprint 6).

Uses a file-backed SQLite database via the app factory so tests exercise the
real HTTP stack (routes -> services -> repositories -> database) without
requiring a running PostgreSQL server.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings

ZONE = {
    "id": "counter",
    "name": "Counter",
    "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings)
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_list_zones(client: TestClient) -> None:
    assert client.post("/zones", json=ZONE).status_code == 201
    zones = client.get("/zones").json()
    assert len(zones) == 1
    assert zones[0]["id"] == "counter"
    assert zones[0]["polygon"] == ZONE["polygon"]


def test_create_duplicate_zone_conflicts(client: TestClient) -> None:
    assert client.post("/zones", json=ZONE).status_code == 201
    assert client.post("/zones", json=ZONE).status_code == 409


def test_create_zone_rejects_invalid_polygon(client: TestClient) -> None:
    bad = {**ZONE, "polygon": [[0, 0], [10, 10]]}
    assert client.post("/zones", json=bad).status_code == 422


def test_record_event_requires_known_zone(client: TestClient) -> None:
    resp = client.post("/events", json=[{"track_id": 1, "zone_id": "nope", "event_type": "enter", "timestamp": 1.0}])
    assert resp.status_code == 404


def test_record_event_bad_type_rejected(client: TestClient) -> None:
    client.post("/zones", json=ZONE)
    resp = client.post("/events", json=[{"track_id": 1, "zone_id": "counter", "event_type": "jump", "timestamp": 1.0}])
    assert resp.status_code == 422


def test_dwell_analytics_flow(client: TestClient) -> None:
    client.post("/zones", json=ZONE)

    sessions = [
        {"track_id": 1, "zone_id": "counter", "enter_time": 10.0, "exit_time": 40.0},
        {"track_id": 2, "zone_id": "counter", "enter_time": 20.0, "exit_time": 60.0},
    ]
    created = client.post("/dwell-sessions", json=sessions)
    assert created.status_code == 201
    assert [s["duration"] for s in created.json()] == [30.0, 40.0]

    analytics = client.get("/analytics/dwell").json()
    assert len(analytics["sessions"]) == 2
    assert analytics["summary"] == [
        {
            "zone_id": "counter",
            "session_count": 2,
            "total_duration": 70.0,
            "average_duration": 35.0,
        }
    ]


def test_dwell_exit_before_enter_rejected(client: TestClient) -> None:
    client.post("/zones", json=ZONE)
    bad = [{"track_id": 1, "zone_id": "counter", "enter_time": 50.0, "exit_time": 40.0}]
    assert client.post("/dwell-sessions", json=bad).status_code == 422
