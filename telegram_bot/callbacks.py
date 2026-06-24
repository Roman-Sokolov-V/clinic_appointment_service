import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from telegram_bot.settings import basic_url
from telegram_bot.api import get_api
from telegram_bot.custom_exeptions import RegistrationFailed, NoTokenFound, BadRequest
from telegram_bot.db.crud import save_refresh_token
from telegram_bot.cash_redis.cash_crud import save_access_token, get_access_token
from telegram_bot.keyboards.keyboards import (
    SlotClick,
    SpecClick,
    PaginationClickSpecializations,
    inline_specializations,
    main_menu_keyboard,
    inline_doctors,
    inline_slots,
    DocClick,
    inline_payment_methods,
    PaymentMethodClick
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

@router.callback_query(F.data == "main_menu_keyboard")
async def to_main_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        text="🏥 Welcome to the Clinic Main Menu.\nSelect an option below:",
        reply_markup=main_menu_keyboard
    )
    await callback.message.delete()

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
            text=f"✅ Слот заброньовано! Будь ласка, [оплатіть замовлення за цим посиланням]({order_data['checkout_url']}).\n\n"
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
