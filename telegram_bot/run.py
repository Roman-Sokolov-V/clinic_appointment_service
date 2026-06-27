import asyncio
import logging
import dotenv

from aiogram import Bot, Dispatcher

from telegram_bot.middlewares import ClinicApiMiddleware
from telegram_bot.settings import TELEGRAM_TOKEN
from telegram_bot.cash_redis.pool import init_redis_pool, close_redis_pool
from telegram_bot.db.pool import init_db_pool, close_db_pool
from telegram_bot.bot.common_callbacks import router as callback_router
from telegram_bot.bot.specializations import specializations_callback_router
from telegram_bot.bot.doctors import doctor_callback_router
from telegram_bot.bot.appointments import appointment_callback_router
from telegram_bot.bot.user import user_router


dotenv.load_dotenv()

bot = Bot(token=TELEGRAM_TOKEN)

dp = Dispatcher()


async def main():
    pool = await init_db_pool()
    redis_client = await init_redis_pool()

    # Реєструємо мідлварь на колбеки та повідомлення
    dp.callback_query.middleware(ClinicApiMiddleware())
    dp.message.middleware(ClinicApiMiddleware())

    dp.include_routers(
        user_router,
        callback_router,
        specializations_callback_router,
        doctor_callback_router,
        appointment_callback_router
    )
    try:
        await dp.start_polling(bot, pool=pool, redis_client=redis_client)
    finally:
        await close_db_pool()  # 👈 закрили pool
        await close_redis_pool()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())