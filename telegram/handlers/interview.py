from aiogram import Router
from aiogram.types import Message

import asyncio

from telegram import logger

interview_router = Router()

@interview_router.message()
async def income_message_processing(message: Message):
    """
    Поведение бота на обычное сообщение пользователя
    """
    if len(message.text) > 200:
        logger.info(f'Старт обработки сообщения от пользователя: "{message.text[:200]}..."')
    else:
        logger.info(f'Старт обработки сообщения от пользователя: "{message.text}"')
    try:
        answer = f"""Тестовый ответ на обычное сообщение"""
        await message.answer(answer)
        logger.info('Успешное звершение ответа')
    except Exception as e:
        logger.error(f'Ошибка ответа на сообщение: {e}')