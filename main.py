import asyncio
from aiogram import Bot, Dispatcher

from config.settings import settings
from telegram import logger
from telegram.handlers.interview import interview_router
from telegram.handlers.commands import commands_router

async def main():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(commands_router)
    dp.include_router(interview_router)

    print('Бот активен и готов принимать сообщения')
    logger.info('Бот активен и готов принимать сообщения')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())