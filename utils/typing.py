import asyncio
from aiogram import Bot
from aiogram.enums import ChatAction


async def send_typing(bot: Bot, chat_id: int, seconds: int = 3):
    end_time = seconds
    while end_time > 0:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(1.5)
        end_time -= 1.5
