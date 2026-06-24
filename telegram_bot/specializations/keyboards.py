from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_bot.common_callback_data_factories import PaginationClickSpecializations
from telegram_bot.common_keyboards import add_next_button, add_main_menu_button
from telegram_bot.specializations.callback_data_factories import SpecClick


def inline_specializations(specializations: list[dict], next: str | None = None):
    """
    функція для динамічного створення кнопок спеціальностей, і кнопки наступної порції пагінованих даних
    """
    keyboard = InlineKeyboardBuilder()
    for sp in specializations:
        keyboard.add(
            InlineKeyboardButton(
                text=sp["name"],
                callback_data=SpecClick(spec_id=sp["id"], spec_name=sp["name"]).pack()
            )
        )
    keyboard.adjust(1)
    if next:
        add_next_button(keyboard, PaginationClickSpecializations.from_url(next_url=next).pack(), "specializations")
    add_main_menu_button(keyboard)
    return keyboard.as_markup()