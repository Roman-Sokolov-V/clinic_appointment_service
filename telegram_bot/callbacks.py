import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

# from telegram_bot.settings import basic_url
from telegram_bot.api import get_api
#from telegram_bot.callback_data_factories import SlotClick
from telegram_bot.custom_exeptions import RegistrationFailed, NoTokenFound, BadRequest
from telegram_bot.db.crud import save_refresh_token
from telegram_bot.cash_redis.cash_crud import save_access_token, get_access_token
from telegram_bot.keyboards.keyboards import (
    # SlotClick,
    # SpecClick,
    # PaginationClickSpecializations,
    # inline_specializations,
    main_menu_keyboard,
    # inline_doctors,
    # inline_slots,
    # DocClick,
    #inline_payment_methods,
    #PaymentMethodClick
)

router = Router()
api_class = get_api()


class Reg(StatesGroup):
    email = State()
    password = State()

class Log(StatesGroup):
    email = State()
    password = State()

class Book(StatesGroup):
    slot_id = State()
    payment_method = State()

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
            reply_markup=main_menu_keyboard
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
        reply_markup=main_menu_keyboard
    )


@router.callback_query(F.data == "main_menu_keyboard")
async def to_main_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        text="🏥 Welcome to the Clinic Main Menu.\nSelect an option below:",
        reply_markup=main_menu_keyboard
    )
    await callback.message.delete()
