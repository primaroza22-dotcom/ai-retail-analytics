"""Vendor-neutral POS domain models.

These dataclasses are the contract every POS adapter produces and the
transaction service consumes. They carry no vendor-specific structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass(frozen=True)
class NormalizedItem:
    product_id: str | None
    sku: str | None
    product_name: str | None
    quantity: float
    unit_price: float
    discount: float = 0.0
    tax: float = 0.0
    line_total: float | None = None


@dataclass(frozen=True)
class NormalizedTransaction:
    external_transaction_id: str
    pos_source: str
    transaction_time: float
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str = "USD"
    payment_method: str | None = None
    status: TransactionStatus = TransactionStatus.COMPLETED
    store_id: str | None = None
    terminal_id: str | None = None
    items: list[NormalizedItem] = field(default_factory=list)
