import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException
from redis.exceptions import RedisError

client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client
    client = redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379/0"),
        decode_responses=True,
    )
    yield
    await client.aclose()


app = FastAPI(lifespan=lifespan)


@app.post("/hit/{key}")
async def hit(key: str):
    try:
        count = await client.incr(f"hit-counter:{key}")
        return {"key": key, "count": count}
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable")


@app.get("/count/{key}")
async def count(key: str):
    try:
        value = await client.get(f"hit-counter:{key}")
        return {"key": key, "count": int(value) if value else 0}
    except RedisError:
        raise HTTPException(status_code=503, detail="Redis unavailable")


@app.get("/healthz")
async def healthz():
    try:
        await client.ping()
        return {"status": "ok", "redis": "up"}
    except (RedisError, AttributeError):
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "redis": "down"},
        )
