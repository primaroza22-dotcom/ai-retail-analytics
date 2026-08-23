"""POS transaction API + idempotency + analytics + WebSocket tests (Sprint 12)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.config import Settings
from backend.database import Base


def _tx(external_id: str, *, pos_source: str = "vendor", total: float = 10.0, **overrides) -> dict:
    payload = {
        "external_transaction_id": external_id,
        "pos_source": pos_source,
        "transaction_time": 1_700_000_000.0,
        "subtotal": total,
        "discount": 0.0,
        "tax": 0.0,
        "total": total,
        "payment_method": "card",
        "items": [{"sku": "SKU-1", "product_name": "Coffee", "quantity": 1, "unit_price": total}],
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as c:
        yield c


# --- CRUD ---


def test_ingest_and_retrieve_transaction(client: TestClient) -> None:
    created = client.post("/transactions/ingest", json=[_tx("T-1")]).json()
    assert len(created) == 1
    assert created[0]["external_transaction_id"] == "T-1"
    assert created[0]["status"] == "completed"

    listed = client.get("/transactions").json()
    assert listed["total"] == 1

    detail = client.get(f"/transactions/{created[0]['id']}").json()
    assert detail["external_transaction_id"] == "T-1"
    assert len(detail["items"]) == 1
    assert detail["items"][0]["sku"] == "SKU-1"


def test_get_transaction_items(client: TestClient) -> None:
    created = client.post("/transactions/ingest", json=[_tx("T-1")]).json()
    items = client.get(f"/transactions/{created[0]['id']}/items").json()
    assert len(items) == 1


def test_ingest_invalid_status_rejected(client: TestClient) -> None:
    resp = client.post("/transactions/ingest", json=[_tx("T-1", status="voided")])
    assert resp.status_code == 422


# --- Idempotency ---


def test_duplicate_ingest_creates_no_duplicate(client: TestClient) -> None:
    client.post("/transactions/ingest", json=[_tx("T-1")])
    client.post("/transactions/ingest", json=[_tx("T-1")])
    assert client.get("/transactions").json()["total"] == 1


def test_same_external_id_different_pos_source_are_distinct(client: TestClient) -> None:
    client.post("/transactions/ingest", json=[_tx("T-1", pos_source="vendor-a")])
    client.post("/transactions/ingest", json=[_tx("T-1", pos_source="vendor-b")])
    assert client.get("/transactions").json()["total"] == 2


# --- Atomicity ---


def test_invalid_item_rolls_back_transaction(client: TestClient) -> None:
    bad = _tx("T-1")
    bad["items"] = [{"sku": "X", "quantity": -1, "unit_price": 5.0}]
    assert client.post("/transactions/ingest", json=[bad]).status_code == 422
    assert client.get("/transactions").json()["total"] == 0


# --- Status lifecycle ---


def test_cancel_and_refund_preserve_record(client: TestClient) -> None:
    created = client.post("/transactions/ingest", json=[_tx("T-1")]).json()
    tx_id = created[0]["id"]

    cancelled = client.patch(f"/transactions/{tx_id}/status", json={"status": "cancelled"}).json()
    assert cancelled["status"] == "cancelled"

    refunded = client.patch(f"/transactions/{tx_id}/status", json={"status": "refunded"}).json()
    assert refunded["status"] == "refunded"

    assert client.get("/transactions").json()["total"] == 1  # record preserved


# --- Analytics ---


def test_transaction_summary_aggregation(client: TestClient) -> None:
    client.post(
        "/transactions/ingest",
        json=[
            _tx("T-1", total=10.0, payment_method="card"),
            _tx("T-2", total=20.0, payment_method="cash"),
        ],
    )
    summary = client.get("/transactions/summary").json()
    assert summary["transaction_count"] == 2
    assert summary["gross_sales"] == 30.0
    assert summary["net_sales"] == 30.0
    assert summary["average_transaction_value"] == 15.0
    assert summary["items_sold"] == 2.0
    methods = {m["payment_method"]: m["count"] for m in summary["by_payment_method"]}
    assert methods == {"card": 1, "cash": 1}


def test_transaction_summary_empty_is_safe(client: TestClient) -> None:
    summary = client.get("/transactions/summary").json()
    assert summary["transaction_count"] == 0
    assert summary["average_transaction_value"] is None
    assert summary["net_sales"] == 0.0


# --- WebSocket events ---


def test_websocket_receives_transaction_created(client: TestClient) -> None:
    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection"
        client.post("/transactions/ingest", json=[_tx("T-1")])
        event = ws.receive_json()
        assert event["type"] == "transaction_created"
        assert event["data"]["external_transaction_id"] == "T-1"
        assert "camera_id" not in event


def test_websocket_receives_transaction_cancelled(client: TestClient) -> None:
    created = client.post("/transactions/ingest", json=[_tx("T-1")]).json()
    with client.websocket_connect("/ws/events") as ws:
        assert ws.receive_json()["type"] == "connection"
        client.patch(f"/transactions/{created[0]['id']}/status", json={"status": "cancelled"})
        event = ws.receive_json()
        assert event["type"] == "transaction_cancelled"
        assert event["data"]["status"] == "cancelled"
