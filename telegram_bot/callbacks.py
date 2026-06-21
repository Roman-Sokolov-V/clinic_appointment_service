import logging

import httpx

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from telegram_bot.settings import basic_url
from telegram_bot.api import get_api
from telegram_bot.custom_exeptions import RegistrationFailed, NoTokenFound, BadRequest
from telegram_bot.db.crud import save_refresh_token
from telegram_bot.cash_redis.cash_crud import save_access_token, get_access_token
import telegram_bot.keyboards as kb

router = Router()
api_class = get_api()


class Reg(StatesGroup):
    email = State()
    password = State()

class Log(StatesGroup):
    email = State()
    password = State()

@router.callback_query(F.data == "register_in_clinic")
async def register_in_clinic(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.email)
    await callback.message.answer("Input email")

@router.message(Reg.email)
async def reg_second(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await state.set_state(Reg.password)
    await message.answer("Input password")

@router.message(Reg.password)
async def reg_third(message: Message, state: FSMContext, pool, redis_client):
    await state.update_data(password=message.text.strip())
    payload = await state.get_data()
    logging.info(payload)
    await state.clear()
    api_service = api_class(message.from_user.id)
    logging.info(payload)
    try:
        user_data = await api_service.register_user(**payload)
        access_token, refresh_token = await api_service.get_tokens(**payload)
        await save_access_token(
            redis_client=redis_client, user_id=message.from_user.id, access_token=access_token
        )
        await save_refresh_token(
            pool=pool, user_id=message.from_user.id, refresh_token=refresh_token
        )
        await message.answer(
            f"Реєстрація успішна! Ваш email: {user_data.get('email')}, password: {payload.get('password')}"
        )
        await message.answer(
            f"Реєстрація успішна! Ваш email: {user_data.get('email')}, password: {payload.get('password')} 👋\n"
            f"Оберіть потрібну послугу клініки:",
            reply_markup=kb.main_menu_keyboard
        )
    except RegistrationFailed as e:
        await message.answer(f"Під час реєстрації сталася помилка {e}")
    except NoTokenFound as e:
        logging.error(f"Під час спроби отримання токенів сталася помилка {e}")
        await message.answer(f"Під час спроби отримання токенів сталася помилка {e}")
    except BadRequest as e:
        await message.answer(f"{e}")



@router.callback_query(F.data == "login_in_clinic")
async def login_in_clinic(callback: CallbackQuery,  state: FSMContext):
    logging.info("Login in clinic first")
    await state.set_state(Log.email)
    await callback.message.answer("Input email")


@router.message(Log.email)
async def log_second(message: Message, state: FSMContext):
    logging.info("Log second")
    await state.update_data(email=message.text.strip())
    await state.set_state(Log.password)
    await message.answer("Input password")

@router.message(Log.password)
async def log_third(message: Message, state: FSMContext, pool, redis_client):
    logging.info("Log third")
    await state.update_data(password=message.text.strip())
    payload = await state.get_data()
    logging.info(payload)
    await state.clear()
    api_service = api_class(message.from_user.id)
    logging.info(payload)
    try:
        access_token, refresh_token = await api_service.get_tokens(**payload)
    except NoTokenFound as e:
        await message.answer(f"Перевірте коректність переданих даних, "
                             f"або якщо ви ще не зареєстровані - спочатку зареєструйтесь. {e}")
    except BadRequest as e:
        await message.answer(f"{e}")

    await save_access_token(
        redis_client=redis_client, user_id=message.from_user.id, access_token=access_token
    )
    await save_refresh_token(
        pool=pool, user_id=message.from_user.id, refresh_token=refresh_token
    )
    await message.answer(
        f"Раді бачити вас знову, {message.from_user.first_name}! 👋\n"
        f"Оберіть потрібну послугу клініки:",
        reply_markup=kb.main_menu_keyboard
    )



#
# @router.callback_query(F.data == "specializations")
# async def show_specializations(callback: CallbackQuery, redis_client):
#     logging.info("Show specializations")
#     user_id = callback.from_user.id
#     api_service = api_class(user_id)
#     access_token = await get_access_token(redis_client=redis_client, user_id=user_id)
#     logging.info( access_token)
#     results, next = await api_service.get_specializations(access_token=access_token)
#
#     await callback.message.answer(
#         reply_markup=kb.inline_specializations(results, next)
#     )
#



# 1. Хендлер для кліку по спеціалізації
@router.callback_query(kb.SpecClick.filter())
async def handle_specialization_click(
        callback: CallbackQuery,
        callback_data: kb.SpecClick,
        redis_client
):
    """
    Робить запит до АПІ, отримує пагіновані дані докторів за обраною спеціалізацією
    :param callback:
    :param callback_data:
    :param redis_client:
    :return:
    """
    await callback.answer()

    # Дістаємо ID спеціалізації прямо з об'єкта callback_data 👇
    spec_id = callback_data.id
    user_id = callback.from_user.id

    await callback.message.answer(f"Ви обрали спеціалізацію з ID: {spec_id}. Шукаю лікарів...")
    await callback.message.answer("Ще трошечки")
    access_token = await get_access_token(redis_client=redis_client, user_id=user_id)
    api_service = api_class(user_id)
    doctors, next = await api_service.get_doctors(access_token=access_token, specialization_id=spec_id)
    await callback.message.answer(
        text=f"Список докторів, клікнувши на обраного доктора отримаєте список вільних слотів",
        reply_markup=kb.inline_doctors(doctors, next)
    )



@router.callback_query(kb.PaginationClickSpecializations.filter())
async def show_specializations(
        callback: CallbackQuery,
        redis_client,
        callback_data: kb.PaginationClickSpecializations,
):
    """
    робить запит до АПІ отримує дані спеціальностей

    """
    logging.info("Show specializations")
    user_id = callback.from_user.id
    api_service = api_class(user_id)
    access_token = await get_access_token(redis_client=redis_client, user_id=user_id)
    logging.info( access_token)

    await callback.answer()

    limit = callback_data.limit
    offset = callback_data.offset
    next_url = None
    if limit and offset:
        next_url = f"{basic_url}/clinic/specializations/?limit={limit}&offset={offset}"

    results, next = await api_service.get_specializations(access_token=access_token, url=next_url)
    if next:
        await callback.message.answer(text=f"{next}")

    await callback.message.answer(
        text="specializations:",
        reply_markup=kb.inline_specializations(results, next)
    )



@router.callback_query(kb.DocClick.filter())
async def show_doctor_detail(
        callback: CallbackQuery,
        redis_client,
        callback_data: kb.PaginationClickSpecializations,
):
    """
    робить запит до АПІ отримує докладні дані доктора

    """
    user_id = callback.from_user.id
    api_service = api_class(user_id)
    access_token = await get_access_token(redis_client=redis_client, user_id=user_id)
    logging.info(access_token)

    await callback.answer()

    doctor_id = callback_data.id

    doctor = await api_service.get_doctor_details(access_token=access_token, doctor_id=doctor_id)


    await callback.message.answer(
        text=f"doctor details: \n"
             f"doctor {doctor['first_name']} {doctor['last_name']}\n"
             f"{doctor['description']}\n"
             f"price per visit: ${doctor['price_per_visit']}\n",
        #reply_markup=kb.inline_slots(doctor.id, next)
    )