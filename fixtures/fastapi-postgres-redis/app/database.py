from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_database_engine() -> AsyncEngine:
    database_url = os.environ["DATABASE_URL"]
    return create_async_engine(database_url, pool_pre_ping=True)
