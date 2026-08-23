"""Alembic migration tests against a fresh SQLite database.

Validates that the version-controlled schema is the source of truth: upgrade
creates the expected tables/indexes, downgrade removes them, and a re-upgrade
works. PostgreSQL-specific behavior is covered by the same migrations when run
against a real server.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine

ROOT = Path(__file__).resolve().parents[1]


def _make_config(url: str) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _table_names(engine: Engine) -> set[str]:
    return set(inspect(engine).get_table_names())


def test_upgrade_creates_expected_schema(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    command.upgrade(_make_config(url), "head")

    engine = create_engine(url)
    tables = _table_names(engine)
    assert {"zones", "zone_events", "dwell_sessions"} <= tables

    inspector = inspect(engine)
    event_indexes = {idx["name"] for idx in inspector.get_indexes("zone_events")}
    for name in (
        "ix_zone_events_track_id",
        "ix_zone_events_zone_id",
        "ix_zone_events_event_type",
        "ix_zone_events_timestamp",
    ):
        assert name in event_indexes, f"missing index {name}"

    dwell_indexes = {idx["name"] for idx in inspector.get_indexes("dwell_sessions")}
    for name in (
        "ix_dwell_sessions_track_id",
        "ix_dwell_sessions_zone_id",
        "ix_dwell_sessions_enter_time",
        "ix_dwell_sessions_status",
    ):
        assert name in dwell_indexes, f"missing index {name}"

    engine.dispose()


def test_downgrade_and_reupgrade(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    cfg = _make_config(url)

    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")

    engine = create_engine(url)
    tables = _table_names(engine)
    assert not {"zones", "zone_events", "dwell_sessions"} & tables
    engine.dispose()

    command.upgrade(cfg, "head")
    engine = create_engine(url)
    assert {"zones", "zone_events", "dwell_sessions"} <= _table_names(engine)
    engine.dispose()
