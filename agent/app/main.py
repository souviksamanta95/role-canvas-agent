from typing import Annotated

import psycopg
import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Response

from app.config import Settings, get_settings

app = FastAPI(title="RoleCanvas Agent")


async def check_redis(settings: Settings) -> bool:
    client = aioredis.from_url(settings.redis_url, socket_connect_timeout=3)
    try:
        return bool(await client.ping())  # type: ignore[misc]
    except Exception:
        return False
    finally:
        await client.aclose()


async def check_postgres(settings: Settings) -> bool:
    try:
        async with await psycopg.AsyncConnection.connect(settings.postgres_dsn) as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception:
        return False


@app.get("/health")
async def health(
    response: Response, settings: Annotated[Settings, Depends(get_settings)]
) -> dict[str, object]:
    redis_ok = await check_redis(settings)
    postgres_ok = await check_postgres(settings)
    ok = redis_ok and postgres_ok
    if not ok:
        response.status_code = 503
    return {
        "status": "ok" if ok else "degraded",
        "service": "agent",
        "checks": {"redis": redis_ok, "postgres": postgres_ok},
    }
