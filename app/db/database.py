from typing import AsyncGenerator
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlalchemy.orm import sessionmaker

# Use aiosqlite for async SQLite connection
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./main.db"
# Note: The connect_args={"check_same_thread": False} is specific to SQLite's default driver
# and is not needed or used by aiosqlite in the same way. aiosqlite handles concurrency properly.

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True, future=True)
# `future=True` enables the newer SQLAlchemy 2.0 style execution model which is preferred.


async def create_db_and_tables():
    async with async_engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Optional: drop tables first
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession]:  # Note the return type hint
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session


# If you need a synchronous engine for any reason (e.g., Alembic migrations not yet async-compatible),
# you might keep it, but primary operations should use the async_engine.
# For this project, we'll aim for full async.
# SYNC_DATABASE_URL = "sqlite:///./test_sync.db"
# sync_engine = create_engine(SYNC_DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
# def create_sync_db_and_tables():
# SQLModel.metadata.create_all(sync_engine)
