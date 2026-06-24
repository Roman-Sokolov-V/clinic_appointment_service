from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from pprint import pprint

from telegram_bot.cash_redis.cash_crud import delete_access_token
from telegram_bot.db.crud import remove_refresh_token


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

@router.message(Command("remove_tokens"))
async def cmd_remove_token(message: Message, pool, redis_client):
    try:
        await delete_access_token(redis_client=redis_client, user_id=message.from_user.id)
        await remove_refresh_token(pool=pool, user_id=message.from_user.id)
        await message.answer("tokens removed")
    except Exception as e:
        await message.answer(str(e))

@router.message(Command("help")) # обробник команди яка передається як аргумент декоратора
async def cmd_help(message: Message):
    await message.answer("this is a help command")

@router.message(F.text == "hello")  # обробник тексту (точне співпадіння)
async def cmd_hello(message: Message):
    await message.answer("Вітаю")




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
