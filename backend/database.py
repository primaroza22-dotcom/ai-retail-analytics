"""Database engine, session factory, and declarative base.

Database access is isolated behind repositories so business logic and route
handlers never touch the engine or session directly.
"""

from __future__ import annotations

from sqlalchemy import Engine, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Declarative base for all ORM models (with a deterministic naming convention)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine_from_url(url: str) -> Engine:
    """Build an engine for the given database URL.

    SQLite needs ``check_same_thread=False`` so a session can be shared with the
    FastAPI test client running on a different thread.
    """
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
