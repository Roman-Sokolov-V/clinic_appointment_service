# import aiohttp
# from aiogram import F, Router
# from aiogram.filters import CommandStart, Command
# from aiogram.types import Message, CallbackQuery
# from pprint import pprint
#
# from telegram_bot.settings import basic_url
#
#
# router = Router()
#
# @router.callback_query(F.data == "doctors")
# async def handle_doctors_query(message: Message, query: CallbackQuery):
#     url = basic_url + "clinic/doctors/"
#
#     async with aiohttp.ClientSession() as session:
#         try:
#             async with session.get(url) as resp:
#                 if resp.status != 200:
#                     doctors = resp.json()
#                     await message.answer(
#                         "doctors",  # todo розпарсити докторів, вивести як таблтцю
#                     )
#                 else:
#                     await message.answer(f"Error: {resp.status}")
#         except aiohttp.ClientError:
#             await message.answer("The server is temporarily unavailable.")

