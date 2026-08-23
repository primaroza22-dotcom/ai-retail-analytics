"""POS adapter + normalizer tests (Sprint 12)."""

from __future__ import annotations

import pytest

from backend.pos import (
    NormalizationError,
    TestPOSAdapter,
    TransactionNormalizer,
    TransactionStatus,
)


def test_test_adapter_returns_deterministic_transactions() -> None:
    adapter = TestPOSAdapter()
    assert adapter.health_check() is True
    transactions = adapter.fetch_transactions()
    assert len(transactions) == 2
    assert transactions[0].external_transaction_id == "POS-1001"
    assert transactions[0].pos_source == "test"
    assert transactions[0].total == 21.2
    assert len(transactions[0].items) == 2


def test_normalizer_normalizes_transaction() -> None:
    raw = {
        "external_transaction_id": "X-1",
        "pos_source": "pos-vendor",
        "transaction_time": 1700000000.0,
        "subtotal": 10.0,
        "discount": 1.0,
        "tax": 0.5,
        "total": 9.5,
        "payment_method": "card",
        "status": "completed",
        "items": [
            {"sku": "SKU-1", "quantity": 2, "unit_price": 5.0},
        ],
    }
    normalized = TransactionNormalizer().normalize(raw)
    assert normalized.external_transaction_id == "X-1"
    assert normalized.status is TransactionStatus.COMPLETED
    assert normalized.items[0].line_total == 10.0  # 2 * 5 - 0 + 0


def test_normalizer_requires_external_id() -> None:
    with pytest.raises(NormalizationError):
        TransactionNormalizer().normalize({"pos_source": "x", "subtotal": 1, "total": 1, "transaction_time": 1})


def test_normalizer_rejects_unknown_status() -> None:
    raw = {
        "external_transaction_id": "X",
        "pos_source": "x",
        "transaction_time": 1,
        "subtotal": 1,
        "total": 1,
        "status": "voided",
    }
    with pytest.raises(NormalizationError):
        TransactionNormalizer().normalize(raw)


def test_normalizer_rejects_invalid_item() -> None:
    raw = {
        "external_transaction_id": "X",
        "pos_source": "x",
        "transaction_time": 1,
        "subtotal": 1,
        "total": 1,
        "items": [{"sku": "S", "quantity": 0, "unit_price": 1}],
    }
    with pytest.raises(NormalizationError):
        TransactionNormalizer().normalize(raw)
