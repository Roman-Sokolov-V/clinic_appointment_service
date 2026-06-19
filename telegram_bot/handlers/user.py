import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from pprint import pprint

import telegram_bot.keyboards as kb
from telegram_bot.cash_redis.cash_crud import get_access_token
from telegram_bot.api.clinic_v1 import ClinicV1
from telegram_bot.custom_exeptions import NotValidToken
from telegram_bot.db.crud import get_refresh_token
from telegram_bot.settings import basic_url

router = Router()

@router.message(Command("me"))
async def cmd_me(message: Message):
    pprint(message.model_dump(exclude_none=True))
    await message.reply(
        text=f"user_name: {message.from_user.username} \n"
             f"first_name: {message.from_user.first_name} \nlast_name: {message.chat.last_name} \n"
             f"id: {message.from_user.id} \n"
             f"language_code: {message.from_user.language_code}"
             f"is_bot: {message.from_user.is_bot}"

    )

@router.message(Command("help")) # обробник команди яка передається як аргумент декоратора
async def cmd_help(message: Message):
    await message.answer("this is a help command")

@router.message(F.text == "hello")  # обробник тексту (точне співпадіння)
async def cmd_hello(message: Message):
    await message.answer("Вітаю")



@router.message(Command("start"))
async def cmd_start(message: Message, pool, redis_client):
    user_id = message.from_user.id

    #  Спроба знайти токен з кешу редіс
    access_token = await get_access_token(redis_client=redis_client, user_id=user_id)

    if not access_token:
        logging.info("Access Token Not Found")
        # Шукаємо рефреш токен в бд
        refresh = await get_refresh_token(pool=pool, user_id=user_id)
        # Якщо нема і його значить юзер не зареєстрований
        if not refresh:
            logging.info("Refresh Token Not Found")
            await message.answer(
                text="Login required",
                reply_markup=kb.register_required_menu
            )
            return
    # я аксес або рефреш токен - показиваємо головне меню
    await message.answer(
        f"Раді бачити вас знову, {message.from_user.first_name}! 👋\n"
        f"Оберіть потрібну послугу клініки:",
        reply_markup=kb.main_menu_keyboard
    )



    # if access_token:
    #     # Токен є в пам'яті — відразу показуємо меню сервісів
    #     await message.answer(
    #         f"Раді бачити вас знову, {message.from_user.first_name}! 👋\n"
    #         f"Оберіть потрібну послугу клініки:",
    #         reply_markup=get_main_menu_keyboard()
    #     )
    #     return
    #
    # # 2. Якщо в пам'яті нема — йдемо в базу даних (Postgres)
    # refresh = await get_token(user_id)
    #
    # if refresh:
    #
    #
    #
    #
    #     # Отримуємо access_token
    #     try:
    #         access_token = ClinicV1.refresh_token(refresh)
    #         # Завантажуємо їх в оперативну пам'ять (FSM)
    #         await state.update_data(
    #             access_token=access_token,
    #         )
    #         await message.answer(
    #             f"Раді бачити вас знову, {message.from_user.first_name}! 👋\n"
    #             f"Оберіть потрібну послугу клініки:",
    #             reply_markup=get_main_menu_keyboard()
    #         )
    #     except NotValidToken:
    #         await message.answer(
    #             text="Login required",
    #             reply_markup=get_not_logined_user_menu()
    #         )
    #     except Exception:
    #         await message.answer(
    #             text="Service not available, try again later",
    #         )
    #
    #
    #
    #
    #     # Завантажуємо їх в оперативну пам'ять (FSM)
    #     await state.update_data(
    #         access_token=tokens["access"],
    #         refresh_token=tokens["refresh"]
    #     )
    #
    #     await message.answer(
    #         f"Авторизацію відновлено! 🔓\n"
    #         f"Оберіть потрібну послугу клініки:",
    #         reply_markup=get_main_menu_keyboard()
    #     )
    # else:
    #     # 3. Токенів немає ніде — користувач неавторизований
    #     await message.answer(
    #         f"Вітаємо у нашому боті клініки! 🏥\n\n"
    #         f"Для того, щоб користуватися сервісами (запис на прийом, перегляд медкарти), "
    #         f"вам потрібно прив'язати свій акаунт клініки до Телеграму.",
    #         reply_markup=get_unauthorized_keyboard()
    #     )

@router.message(Command("help")) # обробник команди яка передається як аргумент декоратора
async def cmd_help(message: Message):
    await message.answer("this is a help command")

@router.message(F.text == "hello")  # обробник тексту (точне співпадіння)
async def cmd_hello(message: Message):
    await message.answer("Вітаю")


##############################
@router.message(F.photo) # обробник присланого фото
async def cmd_photo(message: Message):
    photo_id = message.photo[-1].file_id #  id фото найкращої якості([-1])
    await message.answer(
        f"ID photo: {photo_id}"
    )


@router.message(Command('get_photo'))
async def cmd_get_photo(message: Message):
    await message.answer_photo(
        photo="AgACAgIAAxkBAAMRajEAAWlB9XeDud3CcDlZ18n0QODDAAINHWsbRdCISa9Uf9aA46ZkAQADAgADeAADPAQ", # id фото або посилання
        caption="received photo"
    )
################################
#
# @user.message()
# async def echo(message: Message):
#     await message.send_copy(chat_id=message.from_user.id),
