from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message
import asyncio
from langchain_core.messages import HumanMessage

from telegram import logger
from agents.agents_graph import multi_agent_system

commands_router = Router()


@commands_router.message(Command('start'))
async def start(message: Message, bot: Bot):
    """
    Выводимое сообщение бота при команде /start 
    """
    logger.info('Запуск команды /start')
    try:
        loading_message = await message.answer('Думаю и размышляю...')
        
        initial_state = {
            "messages": [],
            "candidate_name": None,
            "candidate_grade": None,
            "candidate_position": None,
            "current_question_count": 0,
            "interview_status": "active"
        }

        result = await multi_agent_system.ainvoke(
            initial_state | {"messages": [HumanMessage(content="/start")]},
            config={"configurable": {"thread_id": message.chat.id}}
        )
        bot_response = result["messages"][-1].content
        
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=loading_message.message_id,
                              text=bot_response)
        
        logger.info('Успешное выполнение команды /start')
        
    except Exception as e:
        logger.error(f'Ошибка выполнение команды /start: {e}')
    
    
@commands_router.message(Command('stop'))
async def stop(message: Message, bot: Bot):
    """
    Выводимое сообщение и поведение бота при команде /stop 
    """
    logger.info('Запуск команды /stop')
    loading_message = await message.answer('Готовлю сводку и финальный ответ по интервью...')
    
    try:
        result = await multi_agent_system.ainvoke(
            {"messages": [HumanMessage(content="/stop")],
             "interview_status": "finished"
             },
            config={"configurable": {"thread_id": message.chat.id}}
        )
        
        answer = result["messages"][-1].content
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=loading_message.message_id,
                              text=answer)
        logger.info('Успешное выполнение команды /stop')
        
    except Exception as e:
        logger.error(f'Ошибка выполнение команды /stop: {e}')
        answer='Произошла ошибка. Попробуйте позже'
        bot.edit_message_text(chat_id=message.chat.id,
                              message_id=loading_message.message_id,
                              text=answer)