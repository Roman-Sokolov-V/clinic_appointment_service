import logging

import asyncpg

from telegram_bot.settings import POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB

pool: asyncpg.Pool | None = None


async def init_db_pool() -> asyncpg.Pool:
    global pool
    pool = await asyncpg.create_pool(
        user=POSTGRES_USER,  # Зміни на свої девелоперські змінні з .env
        password=POSTGRES_PASSWORD,  # які ми обговорювали
        database=POSTGRES_DB,
        host=POSTGRES_HOST,  # назва сервісу в docker-compose
        port=POSTGRES_PORT,
    )
    # 2. Одразу беремо одне з'єднання з пулу для створення таблиці
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    user_id BIGINT PRIMARY KEY,
                    refresh_token TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
        logging.info("Успішно перевірено/створено таблицю tokens через пул.")

    except Exception as e:
        logging.error(f"Не вдалося створити таблицю при старті: {e}")
    return pool


async def close_db_pool():
    await pool.close()