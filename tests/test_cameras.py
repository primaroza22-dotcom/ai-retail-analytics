"""Camera registry + camera_id propagation/isolation tests (Sprint 11)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.database import Base

CAM_A = {
    "id": "cam-a",
    "name": "Camera A",
    "source_type": "test",
    "source_url": "test://a",
}
CAM_B = {
    "id": "cam-b",
    "name": "Camera B",
    "source_type": "test",
    "source_url": "test://b",
}
ZONE_A = {
    "id": "zone-a",
    "name": "Zone A",
    "camera_id": "cam-a",
    "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
}
ZONE_B = {
    "id": "zone-b",
    "name": "Zone B",
    "camera_id": "cam-b",
    "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as c:
        yield c


# --- Camera CRUD ---


def test_camera_crud_flow(client: TestClient) -> None:
    assert client.post("/cameras", json=CAM_A).status_code == 201

    cameras = client.get("/cameras").json()
    assert len(cameras) == 1
    assert cameras[0]["id"] == "cam-a"
    assert cameras[0]["source_type"] == "test"

    got = client.get("/cameras/cam-a").json()
    assert got["name"] == "Camera A"

    updated = client.put("/cameras/cam-a", json={"name": "Renamed", "location": "Floor 1"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"
    assert updated.json()["location"] == "Floor 1"


def test_camera_duplicate_conflicts(client: TestClient) -> None:
    assert client.post("/cameras", json=CAM_A).status_code == 201
    assert client.post("/cameras", json=CAM_A).status_code == 409


def test_camera_invalid_source_type_rejected(client: TestClient) -> None:
    bad = {**CAM_A, "source_type": "not-a-source"}
    assert client.post("/cameras", json=bad).status_code == 422


def test_camera_disable_soft_delete(client: TestClient) -> None:
    assert client.post("/cameras", json=CAM_A).status_code == 201
    resp = client.delete("/cameras/cam-a")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
    cameras = client.get("/cameras").json()
    assert len(cameras) == 1  # still present (soft delete)


def test_camera_unknown_404(client: TestClient) -> None:
    assert client.get("/cameras/nope").status_code == 404
    assert client.put("/cameras/nope", json={"name": "x"}).status_code == 404
    assert client.delete("/cameras/nope").status_code == 404


def test_camera_status(client: TestClient) -> None:
    client.post("/cameras", json=CAM_A)
    resp = client.get("/cameras/cam-a/status")
    assert resp.status_code == 200
    assert resp.json()["camera_id"] == "cam-a"
    assert resp.json()["status"] == "unknown"


def test_zone_requires_known_camera(client: TestClient) -> None:
    bad_zone = {**ZONE_A, "camera_id": "missing-camera"}
    assert client.post("/zones", json=bad_zone).status_code == 404


# --- camera_id propagation + isolation ---


def test_events_are_camera_scoped(client: TestClient) -> None:
    client.post("/cameras", json=CAM_A)
    client.post("/cameras", json=CAM_B)
    client.post("/zones", json=ZONE_A)
    client.post("/zones", json=ZONE_B)

    created = client.post(
        "/events",
        json=[{"track_id": 7, "zone_id": "zone-a", "event_type": "enter", "timestamp": 10.0}],
    ).json()
    assert created[0]["camera_id"] == "cam-a"

    only_a = client.get("/events?camera_id=cam-a").json()
    only_b = client.get("/events?camera_id=cam-b").json()
    assert only_a["total"] == 1
    assert only_b["total"] == 0


def test_same_track_id_isolated_between_cameras(client: TestClient) -> None:
    client.post("/cameras", json=CAM_A)
    client.post("/cameras", json=CAM_B)
    client.post("/zones", json=ZONE_A)
    client.post("/zones", json=ZONE_B)

    client.post(
        "/events",
        json=[
            {"track_id": 123, "zone_id": "zone-a", "event_type": "enter", "timestamp": 10.0},
            {"track_id": 123, "zone_id": "zone-b", "event_type": "enter", "timestamp": 10.0},
        ],
    )

    a = client.get("/events?camera_id=cam-a&track_id=123").json()
    b = client.get("/events?camera_id=cam-b&track_id=123").json()
    assert a["total"] == 1
    assert b["total"] == 1
    assert a["items"][0]["zone_id"] == "zone-a"
    assert b["items"][0]["zone_id"] == "zone-b"


def test_dwell_sessions_are_camera_scoped(client: TestClient) -> None:
    client.post("/cameras", json=CAM_A)
    client.post("/cameras", json=CAM_B)
    client.post("/zones", json=ZONE_A)
    client.post("/zones", json=ZONE_B)

    client.post(
        "/dwell-sessions",
        json=[{"track_id": 5, "zone_id": "zone-a", "enter_time": 10.0, "exit_time": 40.0}],
    )
    client.post(
        "/dwell-sessions",
        json=[{"track_id": 5, "zone_id": "zone-b", "enter_time": 10.0, "exit_time": 60.0}],
    )

    a = client.get("/analytics/dwell?camera_id=cam-a").json()
    b = client.get("/analytics/dwell?camera_id=cam-b").json()
    assert a["total"] == 1
    assert b["total"] == 1
    assert a["items"][0]["camera_id"] == "cam-a"
    assert b["items"][0]["camera_id"] == "cam-b"

    summary_a = client.get("/analytics/summary?camera_id=cam-a").json()
    assert summary_a["completed_sessions"] == 1
    assert summary_a["average_dwell_seconds"] == 30.0


def test_zone_list_filter_by_camera(client: TestClient) -> None:
    client.post("/cameras", json=CAM_A)
    client.post("/cameras", json=CAM_B)
    client.post("/zones", json=ZONE_A)
    client.post("/zones", json=ZONE_B)

    zones_a = client.get("/zones?camera_id=cam-a").json()
    assert len(zones_a) == 1
    assert zones_a[0]["id"] == "zone-a"
