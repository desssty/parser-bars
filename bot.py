import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from handlers.form import router as form_router
from dotenv import load_dotenv

load_dotenv()


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
