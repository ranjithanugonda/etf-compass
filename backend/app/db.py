"""Database engine and session — lazy-initialized to avoid event loop conflicts."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.app.config import settings

_engine: Any = None
_loop_id: int | None = None
_factory: Any = None


def _get_session_factory() -> Any:
    """Return a session factory, recreating engine if the event loop changed."""
    global _engine, _loop_id, _factory
    try:
        current_loop_id = id(asyncio.get_running_loop())
    except RuntimeError:
        current_loop_id = -1

    if _factory is None or _loop_id != current_loop_id:
        # Old engine is left to GC — calling async dispose from sync is not clean.
        # The old event loop is already gone, so connections will be cleaned up.
        _engine = create_async_engine(settings.database_url, echo=False)
        _factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
        _loop_id = current_loop_id

    return _factory


def async_session() -> Any:
    """Callable proxy — preserves `async with async_session() as s:` API."""
    return _get_session_factory()()


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with async_session() as session:
        yield session
