import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from pprint import pprint

from telegram_bot.cash_redis.cash_crud import delete_access_token
from telegram_bot.db.crud import remove_refresh_token

from telegram_bot.keyboards.keyboards import main_menu_keyboard, reg_log_menu


router = Router()



@router.message(Command("me"))
async def cmd_me(message: Message):
    pprint(message.model_dump(exclude_none=True))
    await message.reply(
        text=f"user_name: {message.from_user.username} \n"
             f"first_name: {message.from_user.first_name} \nlast_name: {message.chat.last_name} \n"
             f"id: {message.from_user.id} \n"
             f"language_code: {message.from_user.language_code}"
             f"is_bot: {message.from_user.is_bot}"

    )

@router.message(Command("remove_tokens"))
async def cmd_remove_token(message: Message, pool, redis_client):
    try:
        await delete_access_token(redis_client=redis_client, user_id=message.from_user.id)
        await remove_refresh_token(pool=pool, user_id=message.from_user.id)
        await message.answer("tokens removed")
    except Exception as e:
        await message.answer(str(e))



@router.message(Command("start"))
async def cmd_start(message: Message, api_service):
    logging.info("Start Command")
    refresh_token = api_service.refresh_token
    if refresh_token:
        await message.answer(
            f"🏥 Welcome to the Clinic Main Menu.\nSelect an option below:",
            reply_markup=main_menu_keyboard
        )
    else: # рефреш токен не існує юзер не зареєстрований
        await message.answer(
            text="Registration required",
            reply_markup=reg_log_menu
        )
        return