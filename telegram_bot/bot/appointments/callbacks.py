import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from telegram_bot.bot.appointments.callback_data_factories import SlotClick, PaymentMethodClick, CancelAppointmentClick
from telegram_bot.bot.appointments.keyboards import inline_payment_methods
from telegram_bot.bot.common_callback_data_factories import PaginationClickMyAppointments
from telegram_bot.settings import basic_url

router = Router()

@router.callback_query(SlotClick.filter())
async def make_appointment(callback: CallbackQuery, callback_data: SlotClick):
    logging.info("Start Make appointment------------------------------")
    await callback.answer()
    slot_id=callback_data.slot_id
    doctor_id = callback_data.doctor_id
    await callback.message.edit_text(
        text="Choose payment method",
        reply_markup=inline_payment_methods(slot_id=slot_id, doctor_id=doctor_id),
        parse_mode="Markdown"
    )


@router.callback_query(PaymentMethodClick.filter())
async def process_payment_and_order(
        callback: CallbackQuery,
        callback_data: PaymentMethodClick,
        api_service
):
    await callback.answer()

    slot_id = callback_data.slot_id
    payment_method = callback_data.method

    # Відправляємо "пісочний годинник", бо запит до АПІ може зайняти секунду
    await callback.message.edit_text(text="🔄 Створюємо ваш запис у базі даних клініки...")

    try:
        # 🔥 Робимо фінальний запит до твого DRF бекенду
        order_data = await api_service.book_appointment(
            slot_id=slot_id,
            payment_method=payment_method
        )
        await callback.message.edit_text(
            text=f"✅ Слот заброньовано! Будь ласка, оплатіть замовлення за цим [посиланням]({order_data['checkout_url']}).\n\n"
                 f"⏰ Оплату необхідно здійснити протягом 24 годин.\n\n"
                 f"🛡️ **Правила скасування:**\n"
                 f"• Не пізніше ніж за {order_data['window_fee']} хвилин до початку — повне повернення коштів.\n"
                 f"• Пізніше, але до початку зустрічі — повернення {100 - order_data['percent_fee']}% вартості.\n"
                 f"• Після початку зустрічі кошти не повертаються.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Failed to create order: {e}")
        await callback.message.edit_text(text="❌ Щось пішло не так при створенні запису. Спробуйте пізніше.")


@router.callback_query(PaginationClickMyAppointments.filter())
async def handle_my_appointments_click(
        callback: CallbackQuery,
        callback_data: PaginationClickMyAppointments,
        api_service
):
    logging.info("Start get my appointments------------------------------")
    await callback.answer()
    limit = callback_data.limit
    offset = callback_data.offset
    next_url = None
    if limit and offset:
        next_url = f"{api_service.appointments_url}?limit={limit}&offset={offset}"

    appointments, next_url = await api_service.get_my_appointments(url=next_url)
    for appointment in appointments:
        text = (
            f"Status: {appointment['status']}\n"
            f"Date: {appointment['slot']['start']}\n"
            f"Doctor: {appointment['slot']['doctor']['first_name']} "
            f"{appointment['slot']['doctor']['last_name']}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Cancel appointment",
                        callback_data=CancelAppointmentClick(
                            appointment_id=appointment["id"]
                        ).pack()
                    )
                ]
            ]
        )

        await callback.message.answer(
            text=text,
            reply_markup=keyboard
        )

@router.callback_query(CancelAppointmentClick.filter())
async def handle_my_appointments_click(
        callback: CallbackQuery,
        callback_data: CancelAppointmentClick,
        api_service
):
    appointment_id = callback_data.appointment_id
    resp = await api_service.cancel_appointment(appointment_id=appointment_id)
    await callback.message.answer(
        text=f"Done{resp}",
    )
