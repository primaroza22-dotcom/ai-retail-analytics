"""POS adapter interface.

Every POS source is accessed through a ``POSAdapter`` implementation. The core
system depends only on this interface and the normalized models — never on a
vendor SDK.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import NormalizedTransaction


class POSAdapter(ABC):
    """A source of normalized POS transactions."""

    source: str

    @abstractmethod
    def health_check(self) -> bool:
        """Return True when the POS source is reachable."""

    @abstractmethod
    def fetch_transactions(self) -> list[NormalizedTransaction]:
        """Return normalized transactions currently available from the source."""
