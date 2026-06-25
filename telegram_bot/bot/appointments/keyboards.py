from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_bot.bot.appointments.callback_data_factories import PaymentMethodClick
from telegram_bot.bot.common_keyboards import add_back_to_main_menu_button


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
    add_back_to_main_menu_button(keyboard)


    keyboard.row(
        InlineKeyboardButton(
            text="⬅️ Back to main menu",
            callback_data="main_menu_keyboard"
        ),
    )

    return keyboard.as_markup()
