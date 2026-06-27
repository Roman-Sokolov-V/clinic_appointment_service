from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery
from aiogram import Router, F

from telegram_bot.bot.common_callback_data_factories import PaginationClickDoctors
from telegram_bot.bot.doctors.callback_data_factores import DocClick
from telegram_bot.bot.doctors.keyboards import inline_slots, inline_doctors
from telegram_bot.bot.specializations.callback_data_factories import SpecClick
from telegram_bot.settings import basic_url

router = Router()


@router.callback_query(DocClick.filter())
async def show_doctor_detail(
        callback: CallbackQuery,
        api_service,
        callback_data: DocClick,
):
    """
    робить запит до АПІ отримує докладні дані доктора, показує їх,
     і запускає функцію отримання і показу вільних слотів inline_slots

    """

    await callback.answer()

    doctor_id = callback_data.doctor_id

    doctor = await api_service.get_doctor_details(doctor_id=doctor_id)

    await callback.message.answer(
        text=f"doctor details: \ndoctor {doctor['first_name']} {doctor['last_name']}\n{doctor['description']}\nprice per visit: ${doctor['price_per_visit']}\n",
        reply_markup= await inline_slots(doctor_id=doctor_id, api_service=api_service, message=callback.message)
    )



@router.callback_query(PaginationClickDoctors.filter())
async def handle_doctors_click(
        callback: CallbackQuery,
        api_service,
        callback_data: PaginationClickDoctors,
):
    """
    Робить запит до АПІ, отримує пагіновані дані докторів за обраною спеціалізацією
    :param callback:
    :param callback_data:
    :return:
    """
    await callback.answer()

    limit = callback_data.limit
    offset = callback_data.offset
    next_url = None
    if limit and offset:
        next_url = f"{basic_url}/clinic/doctors/?limit={limit}&offset={offset}"
    doctors, next_url = await api_service.get_doctors(url=next_url)
    await callback.message.answer(
        text="Список всіх докторів, клікнувши на обраного доктора отримаєте список вільних слотів,"
             "для фільтрації докторів за спеціальностю, поверніться в головне меню і оберіть спеціальність",
        reply_markup=inline_doctors(doctors=doctors, next_url=next_url)
    )