"""Transaction normalizer.

Converts raw external POS data into vendor-neutral ``NormalizedTransaction``
objects, validating required fields and deriving line totals when missing.
"""

from __future__ import annotations

from typing import Any

from .models import NormalizedItem, NormalizedTransaction, TransactionStatus


class NormalizationError(ValueError):
    """Raised when external POS data cannot be normalized."""


def _require_number(data: dict, key: str, *, nonnegative: bool = False) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)):
        raise NormalizationError(f"{key} must be a number")
    result = float(value)
    if nonnegative and result < 0:
        raise NormalizationError(f"{key} must be non-negative")
    return result


class TransactionNormalizer:
    """Validates and normalizes a raw POS transaction dict."""

    def normalize(self, raw: dict[str, Any]) -> NormalizedTransaction:
        if not isinstance(raw, dict):
            raise NormalizationError("transaction must be an object")

        external_transaction_id = raw.get("external_transaction_id")
        pos_source = raw.get("pos_source")
        if not isinstance(external_transaction_id, str) or not external_transaction_id.strip():
            raise NormalizationError("external_transaction_id is required")
        if not isinstance(pos_source, str) or not pos_source.strip():
            raise NormalizationError("pos_source is required")

        status_raw = raw.get("status", "completed")
        try:
            status = TransactionStatus(status_raw)
        except ValueError as exc:
            raise NormalizationError(f"unknown status: {status_raw}") from exc

        subtotal = _require_number(raw, "subtotal", nonnegative=True)
        discount = _require_number(raw, "discount", nonnegative=True) if "discount" in raw else 0.0
        tax = _require_number(raw, "tax", nonnegative=True) if "tax" in raw else 0.0
        total = _require_number(raw, "total", nonnegative=True)

        items = [self._normalize_item(item) for item in raw.get("items", [])]

        return NormalizedTransaction(
            external_transaction_id=external_transaction_id.strip(),
            pos_source=pos_source.strip(),
            store_id=raw.get("store_id"),
            terminal_id=raw.get("terminal_id"),
            transaction_time=_require_number(raw, "transaction_time"),
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total=total,
            currency=raw.get("currency", "USD"),
            payment_method=raw.get("payment_method"),
            status=status,
            items=items,
        )

    @staticmethod
    def _normalize_item(raw: Any) -> NormalizedItem:
        if not isinstance(raw, dict):
            raise NormalizationError("item must be an object")
        quantity = _require_number(raw, "quantity")
        if quantity <= 0:
            raise NormalizationError("quantity must be positive")
        unit_price = _require_number(raw, "unit_price", nonnegative=True)
        discount = _require_number(raw, "discount", nonnegative=True) if "discount" in raw else 0.0
        tax = _require_number(raw, "tax", nonnegative=True) if "tax" in raw else 0.0
        line_total = raw.get("line_total")
        if line_total is None:
            line_total = quantity * unit_price - discount + tax
        return NormalizedItem(
            product_id=raw.get("product_id"),
            sku=raw.get("sku"),
            product_name=raw.get("product_name"),
            quantity=quantity,
            unit_price=unit_price,
            discount=discount,
            tax=tax,
            line_total=float(line_total),
        )
