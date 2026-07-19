from aiogram import Router, Bot
from aiogram.types import Message
from langchain_core.messages import HumanMessage

from telegram import bot_logger
from agents import run_and_trace

interview_router = Router()

@interview_router.message()
async def income_message_processing(message: Message, bot: Bot):
    """
    Поведение бота на обычное сообщение пользователя
    """
    if len(message.text) > 200:
        bot_logger.info(f'Старт обработки сообщения от пользователя: "{message.text[:200]}..."')
    else:
        bot_logger.info(f'Старт обработки сообщения от пользователя: "{message.text}"')
    try:
        loading_message = await message.answer('Думаю и размышляю...')
        try:
            answer = await run_and_trace(
                {'messages': [HumanMessage(content=message.text)]},
                thread_id=message.chat.id
            )
            await bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=loading_message.message_id,
                                        text=answer)
            if len(answer) > 200:
                bot_logger.info(f'Успешное завершение ответа на сообщение пользователя: "{answer[:200]}..."')
            else:
                bot_logger.info(f'Успешное завершение ответа на сообщение пользователя: "{answer}"')
        except Exception as e:
            bot_logger.error(f'Ошибка в работе агента при ответе на сообщение: {e}')
            answer = 'Произошла ошибка. Попробуйте позже'
            await bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=loading_message.message_id,
                                        text=answer)
        
    except Exception as e:
        bot_logger.error(f'Ошибка в работе бота при ответе на сообщение: {e}')