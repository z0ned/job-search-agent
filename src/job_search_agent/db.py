"""SQLite engine/session lifecycle, shared by CLI and future dashboard."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str) -> Engine:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Sprint 1 supports local SQLite only")
    path = database_url[len("sqlite:///"):]
    if path != ":memory:":
        Path(path).expanduser().parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _configure_sqlite(dbapi_connection: object, _connection_record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)
