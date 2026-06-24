from aiogram import Router, F
from aiogram.types import CallbackQuery

from telegram_bot.keyboards.keyboards import  main_menu_keyboard

router = Router()

@router.callback_query(F.data == "main_menu_keyboard")
async def to_main_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        text="🏥 Welcome to the Clinic Main Menu.\nSelect an option below:",
        reply_markup=main_menu_keyboard
    )
    await callback.message.delete()
