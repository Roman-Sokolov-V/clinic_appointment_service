import redis.asyncio as redis

redis_client: redis.Redis | None = None


async def init_redis():
    global redis_client

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )


async def close_redis():
    await redis_client.close()