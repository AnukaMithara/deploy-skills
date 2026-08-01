from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.cache import create_cache_client
from app.database import create_database_engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    engine = create_database_engine()
    cache = create_cache_client()
    application.state.engine = engine
    application.state.cache = cache
    try:
        yield
    finally:
        await cache.aclose()
        await engine.dispose()


app = FastAPI(title="Deploy Skills Redis Fixture", lifespan=lifespan)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "deploy-skills-fastapi-redis", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        async with app.state.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        await app.state.cache.ping()
    except (SQLAlchemyError, RedisError) as exc:
        raise HTTPException(status_code=503, detail="dependency unavailable") from exc
    return {"status": "healthy", "database": "reachable", "redis": "reachable"}
