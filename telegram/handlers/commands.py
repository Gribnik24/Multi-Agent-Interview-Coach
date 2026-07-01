from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import asyncio

commands_router = Router()

@commands_router.message(Command('start'))
async def start(message: Message):
    """
    Выводимое сообщение бота при команде /start 
    """
    answer = """Тестовое сообщение /start"""
    await message.answer(answer)
    
@commands_router.message(Command('stop'))
async def stop(message: Message):
    """
    Выводимое сообщение и поведение бота при команде /stop 
    """
    answer = """Тестовое сообщение /stop"""
    await message.answer(answer)
    
@commands_router.message(Command('restart'))
async def restart(message: Message):
    """
    Выводимое сообщение и поведение бота при команде /restart 
    """
    answer = """Тестовое сообщение /start"""
    await message.answer(answer)
    
@commands_router.message(Command('about'))
async def about(message: Message):
    """
    Выводимое сообщение бота при команде /about 
    """
    answer = """Тестовое сообщение /about"""
    await message.answer(answer)