import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from telegram_bot.common_callback_data_factories import PaginationClickSpecializations
from telegram_bot.cash_redis.cash_crud import get_access_token
from telegram_bot.doctors.keyboards import inline_doctors
#from telegram_bot.keyboards.keyboards import inline_doctors
from telegram_bot.settings import basic_url
from telegram_bot.specializations.callback_data_factories import SpecClick
from telegram_bot.specializations.keyboards import inline_specializations

router = Router()

# 1. Хендлер для кліку по спеціалізації
@router.callback_query(SpecClick.filter())
async def handle_specialization_click(
        callback: CallbackQuery,
        callback_data: SpecClick,
        api_service
):
    """
    Робить запит до АПІ, отримує пагіновані дані докторів за обраною спеціалізацією
    :param callback:
    :param callback_data:
    :return:
    """
    await callback.answer()

    # Дістаємо ID спеціалізації прямо з об'єкта callback_data 👇
    spec_id = callback_data.spec_id
    spec_name = callback_data.spec_name


    await callback.message.answer(f"Ви обрали спеціалізацію: {spec_name}. Шукаю лікарів...")
    await callback.message.answer("Ще трошечки")

    doctors, next = await api_service.get_doctors(specialization_id=spec_id)
    await callback.message.answer(
        text=f"Список докторів з спеціалізацією {spec_name}, клікнувши на обраного доктора отримаєте список вільних слотів",
        reply_markup=inline_doctors(doctors, next)
    )



@router.callback_query(PaginationClickSpecializations.filter())
async def show_specializations(
        callback: CallbackQuery,
        redis_client,
        api_service,
        callback_data: PaginationClickSpecializations,
):
    """
    робить запит до АПІ отримує дані спеціальностей

    """
    logging.info("Show specializations")
    user_id = callback.from_user.id

    access_token = await get_access_token(redis_client=redis_client, user_id=user_id)
    logging.info( access_token)

    await callback.answer()

    limit = callback_data.limit
    offset = callback_data.offset
    next_url = None
    if limit and offset:
        next_url = f"{basic_url}/clinic/specializations/?limit={limit}&offset={offset}"

    results, next = await api_service.get_specializations(url=next_url)
    if next:
        await callback.message.answer(text=f"{next}")

    await callback.message.answer(
        text="specializations:",
        reply_markup=inline_specializations(results, next)
    )
