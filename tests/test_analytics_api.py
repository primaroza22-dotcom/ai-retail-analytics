"""Tests for Sprint 8 analytics endpoints.

Deterministic fixtures: fixed timestamps (Unix epoch seconds) and explicit
durations, so aggregation expectations are exact and free of real-time flakiness.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.database import Base

ZONE_A = {
    "id": "zone-a",
    "name": "Zone A",
    "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
}
ZONE_B = {
    "id": "zone-b",
    "name": "Zone B",
    "polygon": [[0, 0], [200, 0], [200, 200], [0, 200]],
}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as c:
        yield c


def _zone(client: TestClient, zone: dict) -> None:
    assert client.post("/zones", json=zone).status_code == 201


def _sessions(client: TestClient, sessions: list[dict]) -> None:
    assert client.post("/dwell-sessions", json=sessions).status_code == 201


# --- Events ---


def test_events_pagination_and_filters(client: TestClient) -> None:
    _zone(client, ZONE_A)
    events = [
        {"track_id": i, "zone_id": "zone-a", "event_type": "enter" if i % 2 == 0 else "exit", "timestamp": float(i)}
        for i in range(5)
    ]
    assert client.post("/events", json=events).status_code == 201

    page1 = client.get("/events?limit=2&offset=0").json()
    assert page1["total"] == 5
    assert len(page1["items"]) == 2

    page3 = client.get("/events?limit=2&offset=4").json()
    assert len(page3["items"]) == 1

    enters = client.get("/events?event_type=enter").json()
    assert enters["total"] == 3
    assert all(e["event_type"] == "enter" for e in enters["items"])


def test_events_time_filter(client: TestClient) -> None:
    _zone(client, ZONE_A)
    client.post(
        "/events",
        json=[
            {"track_id": 1, "zone_id": "zone-a", "event_type": "enter", "timestamp": 10.0},
            {"track_id": 2, "zone_id": "zone-a", "event_type": "enter", "timestamp": 20.0},
            {"track_id": 3, "zone_id": "zone-a", "event_type": "enter", "timestamp": 30.0},
        ],
    )
    result = client.get("/events?start_time=15&end_time=25").json()
    assert result["total"] == 1
    assert result["items"][0]["track_id"] == 2


# --- Zone management ---


def test_update_zone_fields(client: TestClient) -> None:
    _zone(client, ZONE_A)
    resp = client.put(
        "/zones/zone-a",
        json={"name": "Renamed", "polygon": [[0, 0], [50, 0], [50, 50], [0, 50]]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renamed"
    assert body["polygon"] == [[0, 0], [50, 0], [50, 50], [0, 50]]
    assert body["enabled"] is True


def test_disable_zone_preserves_it(client: TestClient) -> None:
    _zone(client, ZONE_A)
    resp = client.put("/zones/zone-a", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
    zones = client.get("/zones").json()
    assert len(zones) == 1
    assert zones[0]["enabled"] is False


def test_update_unknown_zone_404(client: TestClient) -> None:
    assert client.put("/zones/nope", json={"enabled": False}).status_code == 404


def test_update_zone_requires_field(client: TestClient) -> None:
    _zone(client, ZONE_A)
    assert client.put("/zones/zone-a", json={}).status_code == 422


# --- Ongoing dwell ---


def test_ongoing_dwell_duration_computed(client: TestClient) -> None:
    _zone(client, ZONE_A)
    created = client.post(
        "/dwell-sessions",
        json=[{"track_id": 7, "zone_id": "zone-a", "enter_time": 1000.0}],
    ).json()
    assert created[0]["status"] == "ongoing"
    assert created[0]["exit_time"] is None
    assert created[0]["duration"] == 0.0

    result = client.get("/analytics/dwell?now=1030.0").json()
    assert result["total"] == 1
    item = result["items"][0]
    assert item["status"] == "ongoing"
    assert item["exit_time"] is None
    assert item["duration"] == 30.0


def test_dwell_filter_by_status(client: TestClient) -> None:
    _zone(client, ZONE_A)
    _sessions(
        client,
        [
            {"track_id": 1, "zone_id": "zone-a", "enter_time": 10.0, "exit_time": 40.0},
            {"track_id": 2, "zone_id": "zone-a", "enter_time": 50.0},
        ],
    )
    completed = client.get("/analytics/dwell?status=completed").json()
    assert completed["total"] == 1
    ongoing = client.get("/analytics/dwell?status=ongoing").json()
    assert ongoing["total"] == 1


# --- Aggregates ---


def test_analytics_summary_deterministic(client: TestClient) -> None:
    _zone(client, ZONE_A)
    _sessions(
        client,
        [
            {"track_id": 1, "zone_id": "zone-a", "enter_time": 10.0, "exit_time": 30.0},  # 20
            {"track_id": 2, "zone_id": "zone-a", "enter_time": 20.0, "exit_time": 60.0},  # 40
            {"track_id": 3, "zone_id": "zone-a", "enter_time": 30.0, "exit_time": 90.0},  # 60
            {"track_id": 4, "zone_id": "zone-a", "enter_time": 40.0},  # ongoing
        ],
    )
    summary = client.get("/analytics/summary").json()
    assert summary["total_sessions"] == 4
    assert summary["completed_sessions"] == 3
    assert summary["ongoing_sessions"] == 1
    assert summary["average_dwell_seconds"] == 40.0
    assert summary["max_dwell_seconds"] == 60.0
    assert summary["min_dwell_seconds"] == 20.0


def test_summary_empty_is_safe(client: TestClient) -> None:
    summary = client.get("/analytics/summary").json()
    assert summary["total_sessions"] == 0
    assert summary["average_dwell_seconds"] is None
    assert summary["max_dwell_seconds"] is None
    assert summary["min_dwell_seconds"] is None


def test_zone_analytics_multiple_zones(client: TestClient) -> None:
    _zone(client, ZONE_A)
    _zone(client, ZONE_B)
    _sessions(
        client,
        [
            {"track_id": 1, "zone_id": "zone-a", "enter_time": 10.0, "exit_time": 30.0},  # 20
            {"track_id": 2, "zone_id": "zone-a", "enter_time": 20.0, "exit_time": 60.0},  # 40
            {"track_id": 3, "zone_id": "zone-b", "enter_time": 30.0, "exit_time": 130.0},  # 100
            {"track_id": 4, "zone_id": "zone-b", "enter_time": 40.0, "exit_time": 240.0},  # 200
        ],
    )
    zones = client.get("/analytics/zones").json()
    by_id = {z["zone_id"]: z for z in zones}
    assert by_id["zone-a"]["average_dwell_seconds"] == 30.0
    assert by_id["zone-a"]["total_dwell_seconds"] == 60.0
    assert by_id["zone-b"]["average_dwell_seconds"] == 150.0
    assert by_id["zone-b"]["total_dwell_seconds"] == 300.0
    assert by_id["zone-a"]["zone_name"] == "Zone A"


def test_time_range_filter_summary(client: TestClient) -> None:
    _zone(client, ZONE_A)
    _sessions(
        client,
        [
            {"track_id": 1, "zone_id": "zone-a", "enter_time": 10.0, "exit_time": 30.0},
            {"track_id": 2, "zone_id": "zone-a", "enter_time": 20.0, "exit_time": 40.0},
            {"track_id": 3, "zone_id": "zone-a", "enter_time": 30.0, "exit_time": 50.0},
        ],
    )
    summary = client.get("/analytics/summary?start_time=15&end_time=25").json()
    assert summary["completed_sessions"] == 1
    assert summary["total_sessions"] == 1


def test_daily_analytics(client: TestClient) -> None:
    _zone(client, ZONE_A)
    _sessions(
        client,
        [
            # day 1 (epoch 1970-01-01)
            {"track_id": 1, "zone_id": "zone-a", "enter_time": 5.0, "exit_time": 15.0},  # 10
            {"track_id": 2, "zone_id": "zone-a", "enter_time": 6.0, "exit_time": 26.0},  # 20
            # day 2 (epoch 1970-01-02)
            {"track_id": 3, "zone_id": "zone-a", "enter_time": 86400.0, "exit_time": 86500.0},  # 100
        ],
    )
    daily = client.get("/analytics/daily").json()
    assert len(daily) == 2
    day1 = daily[0]
    assert day1["date"] == "1970-01-01"
    assert day1["sessions"] == 2
    assert day1["average_dwell_seconds"] == 15.0
    assert day1["total_dwell_seconds"] == 30.0
    day2 = daily[1]
    assert day2["date"] == "1970-01-02"
    assert day2["sessions"] == 1
    assert day2["total_dwell_seconds"] == 100.0

    day2_only = client.get("/analytics/daily?start_time=86400&end_time=90000").json()
    assert len(day2_only) == 1
    assert day2_only[0]["date"] == "1970-01-02"


def test_zone_ranking(client: TestClient) -> None:
    _zone(client, ZONE_A)
    _zone(client, ZONE_B)
    _sessions(
        client,
        [
            {"track_id": 1, "zone_id": "zone-a", "enter_time": 10.0, "exit_time": 30.0},  # 20
            {"track_id": 2, "zone_id": "zone-b", "enter_time": 20.0, "exit_time": 120.0},  # 100
        ],
    )
    by_avg = client.get("/analytics/zones/ranking").json()
    assert [z["zone_id"] for z in by_avg] == ["zone-b", "zone-a"]
    assert by_avg[0]["rank"] == 1

    by_total = client.get("/analytics/zones/ranking?metric=total_dwell").json()
    assert [z["zone_id"] for z in by_total] == ["zone-b", "zone-a"]
