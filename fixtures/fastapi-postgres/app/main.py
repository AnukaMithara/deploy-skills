from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import create_database_engine


@asynccontextmanager
async def lifespan(application: FastAPI):
    engine = create_database_engine()
    application.state.engine = engine
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Deploy Skills Fixture", lifespan=lifespan)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "deploy-skills-fastapi", "status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with app.state.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "healthy", "database": "reachable"}
