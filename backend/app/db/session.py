"""SQLAlchemy engine and session management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from threading import Lock
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base


def _normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://") and "+psycopg" not in raw_url:
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


DATABASE_URL = _normalize_database_url(
    os.getenv("DATABASE_URL", "sqlite+pysqlite:///./ev_grid_ops.db")
)

_engine_kwargs: dict = {"future": True, "pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine: Engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

_init_lock = Lock()
_initialized = False


def init_database() -> None:
    """Create all tables for local/dev startup if they do not exist."""
    global _initialized
    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return
        # Import models to ensure SQLAlchemy metadata is fully registered.
        from app.db import models as _models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        _initialized = True


@contextmanager
def session_scope() -> Iterator[Session]:
    """Yield a transactional SQLAlchemy session."""
    init_database()
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

