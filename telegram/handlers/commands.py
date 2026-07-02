from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import asyncio

from telegram import logger

commands_router = Router()


@commands_router.message(Command('start'))
async def start(message: Message):
    """
    Выводимое сообщение бота при команде /start 
    """
    logger.info('Запуск команды /start')
    try:
        answer = """Тестовое сообщение /start"""
        await message.answer(answer)
        logger.info('Успешное выполнение команды /start')
    except Exception as e:
        logger.error(f'Ошибка выполнение команды /start: {e}')
    
    
@commands_router.message(Command('stop'))
async def stop(message: Message):
    """
    Выводимое сообщение и поведение бота при команде /stop 
    """
    logger.info('Запуск команды /stop')
    try:
        answer = """Тестовое сообщение /stop"""
        await message.answer(answer)
        logger.info('Успешное выполнение команды /stop')
    except Exception as e:
        logger.error(f'Ошибка выполнение команды /stop: {e}')
    
    
@commands_router.message(Command('restart'))
async def restart(message: Message):
    """
    Выводимое сообщение и поведение бота при команде /restart 
    """
    logger.info('Запуск команды /restart')
    try:
        answer = """Тестовое сообщение /restart"""
        await message.answer(answer)
        logger.info('Успешное выполнение команды /restart')
    except Exception as e:
        logger.error(f'Ошибка выполнение команды /restart: {e}')
    
    
@commands_router.message(Command('about'))
async def about(message: Message):
    """
    Выводимое сообщение бота при команде /about 
    """
    logger.info('Запуск команды /about')
    try:
        answer = """Тестовое сообщение /about"""
        await message.answer(answer)
        logger.info('Успешное выполнение команды /about')
    except Exception as e:
        logger.error(f'Ошибка выполнение команды /about: {e}')