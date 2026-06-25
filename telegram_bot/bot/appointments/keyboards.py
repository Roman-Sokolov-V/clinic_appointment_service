from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_bot.bot.appointments.callback_data_factories import PaymentMethodClick
from telegram_bot.bot.common_keyboards import add_back_to_main_menu_button
from telegram_bot.bot.appointments.callback_data_factories import CancelAppointmentClick

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


    return keyboard.as_markup()


#
# def inline_appointments(appointments: list[dict], callback: CallbackQuery) -> InlineKeyboardBuilder:
#     keyboard = InlineKeyboardBuilder()
#     for a in appointments:
#
#         keyboard.add(
#             InlineKeyboardButton(
#             text=f"start_date: {a["slot"]['start']}\n"
#                  f"doctor: {a["slot"]['doctor']['first_name']} {a["slot"]['doctor']['last_name']}",
#             callback_data=DetailAppointmentClick(appointment_id=int(a["id"])).pack()
#             )
#
#         )
#
#     keyboard.adjust(2)
#     add_back_to_main_menu_button(keyboard)
#
#     return keyboard.as_markup()

