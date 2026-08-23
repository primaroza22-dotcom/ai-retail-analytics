"""Domain-level exceptions raised by the service layer."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for business-logic errors."""


class NotFoundError(DomainError):
    """A referenced entity does not exist."""


class ConflictError(DomainError):
    """An operation conflicts with existing state."""


class ValidationError(DomainError):
    """Business validation failed."""
