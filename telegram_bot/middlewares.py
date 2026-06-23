import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from telegram_bot.db.crud import get_refresh_token
from telegram_bot.cash_redis.cash_crud import get_access_token, save_access_token
from telegram_bot.api import get_api


class ClinicApiMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Дістаємо юзера, щоб отримати його user_id
        # event може бути Message або CallbackQuery, у обох є event.from_user
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # 2. Дістаємо пул та редіс, які ти передав у start_polling
        pool = data.get("pool")
        redis_client = data.get("redis_client")
        access_token = await get_access_token(redis_client=redis_client, user_id=user.id)
        if access_token:
            logging.info(f"Access Token Found {access_token}")
        refresh_token = await get_refresh_token(pool=pool, user_id=user.id)
        if refresh_token:
            logging.info(f"Refresh Token Found {refresh_token}")
        else:
            logging.info(f"Refresh Token Not Found {refresh_token}")


        # 3. Створюємо екземпляр сервісу ОДИН раз тут автоматично 👇
        api_service = get_api()(
            user_id=user.id,
            pool=pool,
            redis_client=redis_client,
            access_token=access_token,
            refresh_token=refresh_token,
        )
        if refresh_token and not access_token:
            logging.info("try update access_token")
            await api_service.refresh_access_token()


        # 4. Прокидаємо готовий сервіс у контекст хендлерів
        data["api_service"] = api_service

        # Передаємо керування далі хендлеру
        return await handler(event, data)