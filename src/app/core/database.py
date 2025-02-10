"""Database configuration and session management for the application."""

import contextlib
from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models with eager defaults enabled."""

    __mapper_args__: dict[str, Any] = {"eager_defaults": True}  # noqa: RUF012


class DatabaseSessionManager:
    """Manages database connections and sessions for async SQLAlchemy."""

    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None) -> None:
        """Initialize the session manager with database host and engine arguments.

        Args:
            host: Database connection URL.
            engine_kwargs: Additional keyword arguments for async engine creation.

        """
        self._engine: AsyncEngine | None = create_async_engine(host, **(engine_kwargs or {}))
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    async def close(self) -> None:
        """Close the database engine and cleanup session maker."""
        if self._engine is None:
            return
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Asynchronous context manager for database connection.

        Yields:
            AsyncConnection: A connection to the database.

        Raises:
            SQLAlchemyError: If the database engine is not initialized.

        """
        if self._engine is None:
            raise SQLAlchemyError("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except SQLAlchemyError:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Asynchronous context manager for database session.

        Yields:
            AsyncSession: A database session.

        Raises:
            SQLAlchemyError: If the session maker is not initialized.

        """
        if self._sessionmaker is None:
            raise SQLAlchemyError("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except SQLAlchemyError:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def health_check(self) -> bool:
        """Perform a health check on the database connection.

        Returns:
            bool: True if the database is reachable, False otherwise.

        """
        try:
            async with self.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError:
            return False
