from aiogram import Router, Bot
from aiogram.types import Message
import asyncio
from langchain_core.messages import HumanMessage

from telegram import logger
from agents.agents_graph import multi_agent_system

interview_router = Router()

@interview_router.message()
async def income_message_processing(message: Message, bot: Bot):
    """
    Поведение бота на обычное сообщение пользователя
    """
    if len(message.text) > 200:
        logger.info(f'Старт обработки сообщения от пользователя: "{message.text[:200]}..."')
    else:
        logger.info(f'Старт обработки сообщения от пользователя: "{message.text}"')
    try:
        loading_message = await message.answer('Думаю и размышляю...')
        try:
            result = await multi_agent_system.ainvoke(
                {"messages": [HumanMessage(content=message.text)]},
                config={"configurable": {"thread_id": message.chat.id}}
            )
            
            # Берём последнее сообщение — оно от последнего выполненного узла
            answer = result["messages"][-1].content
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=loading_message.message_id,
                                  text=answer)
            logger.info('Успешное завершение ответа на сообщение пользователя')
            
        except Exception as e:
            logger.error(f'Ошибка в работе агента при ответе на сообщение: {e}')
            answer = 'Произошла ошибка. Попробуйте позже'
            bot.edit_message_text(chat_id=message.chat.id,
                                  message_id=loading_message.message_id,
                                  text=answer) 
        
    except Exception as e:
        logger.error(f'Ошибка в работе бота при ответе на сообщение: {e}')