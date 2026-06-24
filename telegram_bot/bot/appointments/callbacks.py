import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from telegram_bot.bot.appointments.callback_data_factories import SlotClick, PaymentMethodClick
from telegram_bot.bot.appointments.keyboards import inline_payment_methods

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
