import logging
import re

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

# Фабрика для вибору конкретної спеціалізації
class SpecClick(CallbackData, prefix="spec"):
    id: int

class DocClick(CallbackData, prefix="doc"):
    id: int

# Фабрика для пагінації (кнопка "Next")
class PaginationClick():
    limit: int | None = None
    offset: int | None = None

class PaginationClickSpecializations(PaginationClick, CallbackData, prefix="page"):
    pass

class PaginationClickDoctors(PaginationClick, CallbackData, prefix="page"):
    pass


main_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
       # [InlineKeyboardButton(text="doctors", callback_data="doctors_data"),],
        [InlineKeyboardButton(text="specializations", callback_data=PaginationClickSpecializations(limit=None, offset=None).pack()), ],
    ],
    resize_keyboard=True,
    input_field_placeholder= "Select a menu item"
)


reg_log_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="register in clinic", callback_data="register_in_clinic"),
            InlineKeyboardButton(text="login in clinic", callback_data="login_in_clinic"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder= "Select a menu item"
)




def inline_specializations(specializations: list[dict], next: str | None = None):
    """
    функція для динамічного створення кнопок спеціальностей, і кнопки наступної порції пагінованих даних
    """
    keyboard = InlineKeyboardBuilder()
    for sp in specializations:
        keyboard.add(
            InlineKeyboardButton(
                text=sp["name"],
                callback_data=SpecClick(id=sp["id"]).pack()
            )
        )

    if next:
        logging.info(f"Next specializations: {next}")
        match = re.search(re.escape("limit=") + r"(\d+)", next)
        if match:
            limit = int(match.group(1))
            logging.info(f"limit: {limit}")
        match = re.search(re.escape("offset=") + r"(\d+)", next)
        if match:
            offset = int(match.group(1))
            logging.info(f"offset: {offset}")
        keyboard.add(
            InlineKeyboardButton(
                text="Show next specializations ⏭️",
                callback_data=PaginationClickSpecializations(limit=limit, offset=offset).pack()
            )
        )
    return keyboard.adjust(1).as_markup()




def inline_doctors(doctors: list[dict], next: str | None = None):
    """
    функція для динамічного створення кнопок докторів, і кнопки наступної порції пагінованих даних
    """
    keyboard = InlineKeyboardBuilder()
    for doc in doctors:
        keyboard.add(
            InlineKeyboardButton(
                text=f"{doc["first_name"]} {doc['last_name']}",
                callback_data=DocClick(id=doc["id"]).pack()
            )
        )

    if next:
        logging.info(f"Next doctors: {next}")
        match = re.search(re.escape("limit=") + r"(\d+)", next)
        if match:
            limit = int(match.group(1))
            logging.info(f"limit: {limit}")
        match = re.search(re.escape("offset=") + r"(\d+)", next)
        if match:
            offset = int(match.group(1))
            logging.info(f"offset: {offset}")
        keyboard.add(
            InlineKeyboardButton(
                text="Show next doctors ⏭️",
                callback_data=PaginationClickDoctors(limit=limit, offset=offset).pack()
            )
        )
    return keyboard.adjust(1).as_markup()