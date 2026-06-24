from aiogram.types import CallbackQuery
from aiogram import Router

from telegram_bot.callback_data_factories import DocClick
from telegram_bot.keyboards.keyboards import inline_slots

router = Router()


@router.callback_query(DocClick.filter())
async def show_doctor_detail(
        callback: CallbackQuery,
        api_service,
        callback_data: DocClick,
):
    """
    робить запит до АПІ отримує докладні дані доктора

    """

    await callback.answer()

    doctor_id = callback_data.doctor_id

    doctor = await api_service.get_doctor_details(doctor_id=doctor_id)

    await callback.message.answer(
        text=f"doctor details: \ndoctor {doctor['first_name']} {doctor['last_name']}\n{doctor['description']}\nprice per visit: ${doctor['price_per_visit']}\n",
        reply_markup= await inline_slots(doctor_id=doctor_id, api_service=api_service, message=callback.message)
    )