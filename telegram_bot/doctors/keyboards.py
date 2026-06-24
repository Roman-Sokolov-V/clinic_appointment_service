import logging

from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_bot.api.base import ApiService
from telegram_bot.callback_data_factories import PaginationClickDoctors, SlotClick, PaginationClickSlots
from telegram_bot.doctors.callback_data_factores import DocClick
from telegram_bot.keyboards.common import add_next_button, add_main_menu_button


def inline_doctors(doctors: list[dict], next: str | None = None):
    """
    функція для динамічного створення кнопок докторів, і кнопки наступної порції пагінованих даних
    """
    keyboard = InlineKeyboardBuilder()
    for doc in doctors:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{doc["first_name"]} {doc['last_name']}",
                callback_data=DocClick(doctor_id=doc["id"]).pack()
            )
        )
    keyboard.adjust(1)
    if next:
        add_next_button(keyboard, PaginationClickDoctors.from_url(next_url=next).pack(), "doctors")

    add_main_menu_button(keyboard)
    return keyboard.as_markup()

async def inline_slots(doctor_id: int, api_service: ApiService, message: Message):

    slots, next = await api_service.get_doctor_slots(doctor_id=doctor_id)
    logging.info(f"Slots: {slots}")
    keyboard = InlineKeyboardBuilder()
    if not slots:
        await message.answer(text="No slots available for this doctor.")
        return None
    if slots:
        for slot in slots:
            keyboard.add(
                InlineKeyboardButton(
                    text=f"start: {slot['start']}  end: {slot['end']}    press to make appointment",
                    callback_data=SlotClick(slot_id=slot["id"], doctor_id=doctor_id).pack()
                ),
            )
    keyboard.adjust(1)
    if next:
        logging.info(f"Next slots: {next}")
        add_next_button(keyboard, PaginationClickSlots.from_url(next_url=next).pack(), "slots")
    add_main_menu_button(keyboard)
    return keyboard.as_markup()