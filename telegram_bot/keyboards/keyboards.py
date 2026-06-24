import logging
import re
from operator import add

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

from telegram_bot.api.base import ApiService
from telegram_bot.callback_data_factories import PaginationClickSpecializations, SpecClick, DocClick, \
    PaginationClickDoctors, SlotClick, PaginationClickSlots, PaymentMethodClick
from telegram_bot.keyboards.common import add_main_menu_button, add_next_button

#
# # Фабрика для вибору конкретної спеціалізації
# class SpecClick(CallbackData, prefix="spec"):
#     id: int
#
# class DocClick(CallbackData, prefix="doc"):
#     id: int
#
# class SlotClick(CallbackData, prefix="slot"):
#     slot_id: int
#     doctor_id: int
#
# class PaymentMethodClick(CallbackData, prefix="pay_method"):
#     slot_id: int
#     method: str
#
# # Фабрика для пагінації (кнопка "Next")
# class PaginationClick():
#     limit: int | None = None
#     offset: int | None = None
#
#     @classmethod
#     def from_url(cls, next_url: str | None = None) -> 'PaginationClick':
#         if not next_url:
#             return cls(limit=None, offset=None)
#         limit_match = re.search(r"limit=(\d+)", next_url)
#         offset_match = re.search(r"offset=(\d+)", next_url)
#         return cls(
#             limit=int(limit_match.group(1)) if limit_match else None,
#             offset=int(offset_match.group(1)) if offset_match else None
#         )
#
# class PaginationClickSpecializations(PaginationClick, CallbackData, prefix="spec"):
#     pass
#
# class PaginationClickDoctors(PaginationClick, CallbackData, prefix="doc"):
#     pass
#
# class PaginationClickSlots(PaginationClick, CallbackData, prefix="slot"):
#     pass

main_menu_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
       # [InlineKeyboardButton(text="doctors", callback_data="doctors_data"),],
        [InlineKeyboardButton(text="specializations", callback_data=PaginationClickSpecializations().pack()), ],
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
                callback_data=SpecClick(spec_id=sp["id"], spec_name=sp["name"]).pack()
            )
        )
    keyboard.adjust(1)
    if next:
        add_next_button(keyboard, PaginationClickSpecializations.from_url(next_url=next).pack(), "specializations")
    add_main_menu_button(keyboard)
    return keyboard.as_markup()




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


def inline_payment_methods(slot_id: int, doctor_id: int) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()

    keyboard.add(
        InlineKeyboardButton(
            text="💳 Оплата карткою (Stripe)",
            callback_data=PaymentMethodClick(slot_id=slot_id, method="STRIPE").pack()
        ),
        InlineKeyboardButton(
            text="💳 Оплата карткою (Тут повинен бути інший метод, але реалізовано тільки Stripe)",
            callback_data=PaymentMethodClick(slot_id=slot_id, method="STRIPE").pack()
        )
    )

    keyboard.adjust(1)
    add_main_menu_button(keyboard)
    # # Кнопка скасування (повернення назад до лікаря/слотів)
    # keyboard.row(
    #     InlineKeyboardButton(
    #         text="❌ Return to previous menu",
    #         callback_data="main_menu_keyboard"
    #     )
    # )

    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Back to main menu",
            callback_data="main_menu_keyboard"
        ),
    )



    return keyboard.adjust(1).as_markup()
