import redis.asyncio as aioredis
from telegram_bot.settings import REDIS_URL


redis_client: aioredis.Redis | None = None

async def init_redis_pool()-> aioredis.Redis:
    global redis_pool, redis_client
    redis_pool = aioredis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
    return  aioredis.Redis(connection_pool=redis_pool)

async def close_redis_pool():
    global redis_pool
    if redis_pool:
        await redis_pool.disconnect()



