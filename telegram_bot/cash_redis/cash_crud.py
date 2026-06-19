from telegram_bot.custom_exeptions import TokenNotExists
from telegram_bot.settings import TOKEN_LIFETIME


async def save_access_token(redis_client, user_id: int, access_token: str):
    await redis_client.set(
        name=str(user_id),
        value=access_token,
        ex=TOKEN_LIFETIME - 1
    )

async def get_access_token(redis_client, user_id: int):
    access_token = await redis_client.get(
         name=str(user_id)
    )
    return access_token


async def delete_access_token(redis_client, user_id: int):
    await redis_client.delete(str(user_id))