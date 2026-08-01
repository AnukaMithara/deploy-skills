from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def create_database_engine() -> Engine:
    database_url = os.environ["DATABASE_URL"]
    return create_engine(database_url, pool_pre_ping=True)
