from aiogram import Router
from aiogram.types import Message

import asyncio

interview_router = Router()

@interview_router.message()
async def income_message_processing(message: Message):
    answer = f"""Тестовый ответ на обычное сообщение"""
    await message.answer(answer)