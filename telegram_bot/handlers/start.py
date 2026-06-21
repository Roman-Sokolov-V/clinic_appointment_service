import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from pprint import pprint

import telegram_bot.keyboards as kb
from telegram_bot.api import get_api
from telegram_bot.custom_exeptions import BadRequest
from telegram_bot.cash_redis.cash_crud import get_access_token, delete_access_token, save_access_token
from telegram_bot.api.clinic_v1 import ClinicV1
from telegram_bot.custom_exeptions import NotValidToken
from telegram_bot.db.crud import get_refresh_token
from telegram_bot.settings import basic_url

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message, pool, redis_client):
    logging.info("Start Command")
    user_id = message.from_user.id

    #  Спроба знайти токен з кешу редіс
    access_token = await get_access_token(redis_client=redis_client, user_id=user_id)
    if access_token:
        logging.info(f"Access Token Found {access_token}")
        await message.answer(
            f"Раді бачити вас знову, {message.from_user.first_name}! 👋\n"
            f"Оберіть потрібну послугу клініки:",
            reply_markup=kb.main_menu_keyboard
        )
    else: # access token не існує або видалений через вичерпання терміну дії
        logging.info("Access Token Not Found")
        # Шукаємо рефреш токен в бд
        refresh = await get_refresh_token(pool=pool, user_id=user_id)

        if not refresh: # Якщо нема і його значить юзер не зареєстрований
            logging.info("Refresh Token Not Found")
            await message.answer(
                text="Registration required",
                reply_markup=kb.reg_log_menu
            )
            return
        else: # рефреш є
            logging.info("Refresh Token Found")
            api = get_api()(user_id)
            try: # спроба оновити access token
                logging.info("Trying to refresh access token")
                access_token = await api.refresh_access_token(refresh_token=refresh)
                logging.info(f"new access token {access_token}")
                await save_access_token(
                    redis_client=redis_client, user_id=user_id, access_token=access_token
                )
                await message.answer(
                    f"Раді бачити вас знову, {message.from_user.first_name}! 👋\n"
                    f"Оберіть потрібну послугу клініки:",
                    reply_markup=kb.main_menu_keyboard
                )
            except NotValidToken: # рефреш токен не дійсний або прострочений
                logging.error("Not valid refresh token")
                await message.answer("Login required", reply_markup=kb.reg_log_menu)


