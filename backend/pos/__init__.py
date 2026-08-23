"""POS integration layer (Sprint 12).

Vendor-neutral adapter interface, transaction normalizer, and a deterministic
test adapter. Future adapters (REST, webhook, database, CSV, vendor SDKs) all
implement ``POSAdapter``.
"""

from .adapter import POSAdapter
from .models import NormalizedItem, NormalizedTransaction, TransactionStatus
from .normalizer import NormalizationError, TransactionNormalizer
from .test_adapter import TestPOSAdapter

__all__ = [
    "NormalizationError",
    "NormalizedItem",
    "NormalizedTransaction",
    "POSAdapter",
    "TestPOSAdapter",
    "TransactionNormalizer",
    "TransactionStatus",
]
