import logging

import httpx

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from telegram_bot.db.crud import save_refresh_token
from telegram_bot.cash_redis.cash_crud import save_access_token
from telegram_bot.settings import REG_URL, TOKEN_URL

router = Router()

class Reg(StatesGroup):
    email = State()
    password = State()

#
# @router.callback_query(F.data == "doctors_data")
# async def confirm_handler(callback: CallbackQuery):
#
#     await callback.answer("OK")

@router.callback_query(F.data == "register_in_clinic")
async def register_in_clinic(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Reg.email)
    await callback.message.answer("Input email")
    # input email, password
    # requst to clinic register
    # request to clinic get tokens
    # write tokens to redis and db
    # return main menu keyboard

@router.message(Reg.email)
async def reg_second(message: Message, state: FSMContext):
    await state.update_data(email=message.text.strip())
    await state.set_state(Reg.password)
    await message.answer("Input password")

@router.message(Reg.password)
async def reg_third(message: Message, state: FSMContext, pool, redis_client):
    await state.update_data(password=message.text.strip())
    # await state.set_state(Reg.password)
    payload = await state.get_data()
    await state.clear()
    #await message.answer(f"You have input {payload['email']} {payload['password']}")
    try:
        # 🎯 4. Робимо АСИНХРОННИЙ запит через AsyncClient
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=REG_URL,
                json=payload,  # 🔥 Передаємо як json, а не data
                timeout=10.0  # Хороша практика — ставити таймаут, щоб бот не чекав вічно
            )

            # 5. Перевіряємо статус
            if response.status_code == 201:
                user_data = response.json()
                # Отримуємо jwt tokens
                response = await client.post(
                    url=TOKEN_URL,
                    json=payload,
                    timeout=10.0
                )
                if response.status_code in (200, 201):
                    access_token = response.json()["access"]
                    refresh_token = response.json()["refresh"]
                    await save_access_token(
                        redis_client=redis_client, user_id=message.from_user.id, access_token=access_token
                    )
                    await save_refresh_token(
                        pool=pool, user_id=message.from_user.id, refresh_token=refresh_token
                    )

                await message.answer(
                    f"Реєстрація успішна! Ваш email: {user_data.get('email')}, password: {payload.get('password')}"
                )
            else:
                # Якщо бекенд повернув помилку (наприклад, 400 Bad Request, email вже існує)
                logging.warning(f"Помилка бекенду: {response.status_code} - {response.text}")
                await message.answer("Не вдалося зареєструватися. Перевірте введені дані.")

    except httpx.RequestError as e:
        # Обробляємо випадок, якщо сам бекенд клініки лежить/недоступний
        logging.error(f"Помилка зв'язку з сервером: {e}")
        await message.answer("Сервер реєстрації тимчасово недоступний. Спробуйте пізніше.")