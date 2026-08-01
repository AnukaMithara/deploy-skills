from __future__ import annotations

import os

import redis.asyncio as redis


def create_cache_client() -> redis.Redis:
    pool = redis.ConnectionPool.from_url(
        os.environ["REDIS_URL"],
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    return redis.Redis.from_pool(pool)
