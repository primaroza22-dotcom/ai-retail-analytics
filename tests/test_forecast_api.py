"""Forecast API + WebSocket integration tests (Sprint 13)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.database import Base
from backend.models import Camera, DwellSession, Transaction, Zone, ZoneEvent

DAY = 86400
EPOCH = 1_700_000_000.0


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as c:
        yield c


def _seed(app, days: int = 30) -> None:
    factory = app.state.session_factory
    with factory() as session:
        camera = Camera(id="cam-1", name="Cam", source_type="test")
        zone = Zone(id="z1", name="Zone", camera_id="cam-1", polygon=[[0, 0], [1, 0], [1, 1], [0, 1]])
        session.add(camera)
        session.add(zone)
        for i in range(days):
            day = EPOCH + i * DAY
            for track in range(i + 1):
                session.add(
                    ZoneEvent(camera_id="cam-1", track_id=track, zone_id="z1", event_type="enter", timestamp=day)
                )
            session.add(
                DwellSession(
                    camera_id="cam-1", track_id=0, zone_id="z1",
                    enter_time=day, exit_time=day + 60, duration=60.0, status="completed",
                )
            )
            session.add(
                Transaction(
                    external_transaction_id=f"T-{i}", pos_source="vendor",
                    transaction_time=day, subtotal=100.0 * (i + 1), discount=0.0, tax=0.0,
                    total=100.0 * (i + 1), currency="USD", payment_method="card", status="completed",
                )
            )
        session.commit()


# --- Empty / insufficient history ---


def test_forecast_insufficient_history_empty(client: TestClient) -> None:
    resp = client.get("/forecast?target=net_sales").json()
    assert resp["status"] == "insufficient_history"
    assert resp["available"] == 0


def test_forecast_models(client: TestClient) -> None:
    models = client.get("/forecast/models").json()["models"]
    assert len(models) == 4
    assert {m["name"] for m in models} == {"naive", "seasonal_naive", "moving_average", "linear_regression"}


def test_analytics_today_empty(client: TestClient) -> None:
    today = client.get("/analytics/today").json()
    assert today["transactions"] == 0
    assert today["net_sales"] == 0.0
    assert today["traffic"] == 0.0


# --- Seeded data ---


def test_forecast_with_seeded_data(client: TestClient) -> None:
    _seed(client.app)
    resp = client.get("/forecast?target=net_sales&horizon=7").json()
    assert resp["status"] == "ok"
    assert resp["horizon"] == 7
    assert len(resp["forecast"]) == 7
    assert resp["model"] in {"naive", "seasonal_naive", "moving_average", "linear_regression"}
    assert all(p["predicted_value"] >= 0 for p in resp["forecast"])


def test_forecast_evaluation_returns_all_candidates(client: TestClient) -> None:
    _seed(client.app)
    resp = client.get("/forecast/evaluation?target=net_sales").json()
    assert resp["status"] == "ok"
    assert len(resp["results"]) == 4
    assert resp["results"][0]["mae"] <= resp["results"][-1]["mae"]


def test_forecast_camera_aware(client: TestClient) -> None:
    _seed(client.app)
    resp = client.get("/forecast?target=traffic&camera_id=cam-1").json()
    assert resp["status"] == "ok"
    assert len(resp["forecast"]) == 7


def test_analytics_trends_correlations(client: TestClient) -> None:
    _seed(client.app)
    trends = client.get("/analytics/trends").json()
    assert len(trends) > 0
    correlations = client.get("/analytics/correlations").json()
    assert len(correlations) > 0


def test_analytics_anomalies_and_insights(client: TestClient) -> None:
    _seed(client.app)
    anomalies = client.get("/analytics/anomalies").json()
    assert isinstance(anomalies, list)
    insights = client.get("/analytics/insights").json()
    assert isinstance(insights, list)


def test_analytics_today_counts_today(client: TestClient) -> None:
    _seed(client.app)
    with client.app.state.session_factory() as session:
        session.add(
            Transaction(
                external_transaction_id="T-TODAY", pos_source="vendor",
                transaction_time=time.time(), subtotal=50.0, discount=0.0, tax=0.0,
                total=50.0, currency="USD", payment_method="card", status="completed",
            )
        )
        session.commit()
    today = client.get("/analytics/today").json()
    assert today["transactions"] == 1
    assert today["net_sales"] == 50.0


# --- WebSocket events ---


def test_websocket_forecast_refresh_publishes_events(client: TestClient) -> None:
    _seed(client.app)
    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection"
        client.post("/forecast/refresh")
        received = []
        for _ in range(3):
            received.append(ws.receive_json()["type"])
        assert "forecast_updated" in received
