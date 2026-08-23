"""Deterministic POS adapter for automated tests and development."""

from __future__ import annotations

from .adapter import POSAdapter
from .models import NormalizedItem, NormalizedTransaction, TransactionStatus


def _default_transactions() -> list[NormalizedTransaction]:
    return [
        NormalizedTransaction(
            external_transaction_id="POS-1001",
            pos_source="test",
            transaction_time=1_700_000_000.0,
            subtotal=24.0,
            discount=4.0,
            tax=1.2,
            total=21.2,
            currency="USD",
            payment_method="card",
            status=TransactionStatus.COMPLETED,
            terminal_id="T-01",
            items=[
                NormalizedItem(
                    product_id="P-A", sku="A-001", product_name="Coffee",
                    quantity=2.0, unit_price=5.0, discount=0.0, tax=0.5, line_total=10.5,
                ),
                NormalizedItem(
                    product_id="P-B", sku="B-001", product_name="Croissant",
                    quantity=1.0, unit_price=10.0, discount=0.0, tax=0.7, line_total=10.7,
                ),
            ],
        ),
        NormalizedTransaction(
            external_transaction_id="POS-1002",
            pos_source="test",
            transaction_time=1_700_000_100.0,
            subtotal=8.0,
            discount=0.0,
            tax=0.4,
            total=8.4,
            currency="USD",
            payment_method="cash",
            status=TransactionStatus.COMPLETED,
            terminal_id="T-01",
            items=[
                NormalizedItem(
                    product_id="P-A", sku="A-001", product_name="Coffee",
                    quantity=1.0, unit_price=8.0, discount=0.0, tax=0.4, line_total=8.4,
                ),
            ],
        ),
    ]


class TestPOSAdapter(POSAdapter):
    """Returns a fixed, deterministic set of transactions."""

    __test__ = False  # not a pytest test class

    source = "test"

    def __init__(self, transactions: list[NormalizedTransaction] | None = None) -> None:
        self._transactions = list(transactions) if transactions is not None else _default_transactions()

    def health_check(self) -> bool:
        return True

    def fetch_transactions(self) -> list[NormalizedTransaction]:
        return list(self._transactions)
