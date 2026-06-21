#from telegram_bot.db.pool import pool


async def save_refresh_token(pool, user_id: int, refresh_token: str)-> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tokens (user_id, refresh_token)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET refresh_token = EXCLUDED.refresh_token
            """,
            user_id,
            refresh_token,
        )



async def get_refresh_token(pool, user_id: int) -> str:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT refresh_token
            FROM tokens
            WHERE user_id = $1
            """,
            user_id
        )


async def is_user_exists(pool, user_id: int) -> bool:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT EXISTS(SELECT 1 FROM tokens WHERE user_id = $1);
            """,
            user_id
        )

async def remove_refresh_token(pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """DELETE FROM tokens WHERE user_id = $1""", user_id
        )