import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from telegram_bot.keyboards.keyboards import main_menu_keyboard, reg_log_menu


router = Router()

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


