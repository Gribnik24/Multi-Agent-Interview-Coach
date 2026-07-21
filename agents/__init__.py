import time
import json
import logging
import os
import asyncio

# Настройка TAO логгера (логи TAO цикла всей мультиагентной системы)
tao_logger = logging.getLogger('tao_logs')
tao_logger.setLevel(logging.INFO)
tao_logger.propagate = False
tao_logger.handlers.clear()

# Создание папки logs/ в корне проекта при её отсутствии
_current_dir = os.path.dirname(__file__)
_log_dir = os.path.abspath(os.path.join(_current_dir, '..', 'logs'))
os.makedirs(_log_dir, exist_ok=True)

# Файловый обработчик для TAO логов
_tao_log_file = os.path.join(_log_dir, 'tao_logs.log')
_tao_handler = logging.FileHandler(
    filename=_tao_log_file,
    mode='a',
    encoding='utf-8'
)
_tao_handler.setFormatter(
    logging.Formatter('%(levelname)s | %(message)s')
)
tao_logger.addHandler(_tao_handler)

from agents.agents_graph import multi_agent_system

async def collect_tao_logs(result: dict) -> None:
    """
    Фоновый сбор TAO логов мультиагентной системы.
    Обходит сообщения, сгенерированные агентами с момента последнего
    пользовательского запроса, и логирует Think/Act/Observe шаги.
    """
    try:
        all_messages = result.get('messages', [])

        # Формируем срез сообщений с момента последнего пользовательского запроса
        last_human_idx = -1
        for i, msg in enumerate(all_messages):
            if type(msg).__name__ == 'HumanMessage':
                last_human_idx = i
        current_messages = all_messages[max(last_human_idx, 0):]

        # Обрабатываем диалог
        for msg in current_messages:
            msg_type = type(msg).__name__

            if msg_type == 'HumanMessage':
                tao_logger.info(f'[TAO - HUMAN MESSAGE]: {msg.content}')

            elif msg_type == 'AIMessage' and hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tc in msg.tool_calls:
                    # Think (reasoning), если присутствует
                    if not msg.content and msg.additional_kwargs:
                        reasoning = msg.additional_kwargs.get('reasoning_content')
                        if reasoning:
                            tao_logger.info(f'[TAO - THOUGHT]: {reasoning}')
                    tao_logger.info(f'[TAO - ACTION]: {tc["name"]}({json.dumps(tc["args"], ensure_ascii=False)})')

            elif msg_type == 'ToolMessage':
                tao_logger.info(f'[TAO - OBSERVATION]: {msg.content}')

            elif msg_type == 'AIMessage' and not getattr(msg, 'tool_calls', None):
                if msg.content:
                    tao_logger.info(f'[TAO - FINAL ANSWER]: {msg.content}')

    except Exception as e:
        tao_logger.error(f'Ошибка при сборе TAO логов: {e}', exc_info=True)


async def run_and_trace(input_data: dict, thread_id):
    """
    Запуск мультиагентной системы и сбор TAO логов в фоне.
    Возвращает финальный ответ пользователю.
    """
    result = None
    try:
        result = await multi_agent_system.ainvoke(
            input_data,
            config={'configurable': {'thread_id': str(thread_id)}}
        )
        tao_logger.info('[TAO] Передача сообщения и получения ответа от агента завершилась успешно')
    except Exception as e:
        tao_logger.error(f'[TAO] Передача сообщения и получения ответа от агента завершилась ошибкой: {e}', exc_info=True)
        raise

    if result is None:
        tao_logger.error('Ошибка: агент не вернул результат')
        return 'Ошибка: агент не вернул результат'

    # Получаем финальный ответ для пользователя
    user_response = 'Ошибка: нет сообщений в ответе'
    if 'messages' in result and len(result['messages']) > 0:
        last_message = result['messages'][-1]
        if hasattr(last_message, 'content') and last_message.content:
            user_response = last_message.content

    # Запускаем фоновый сбор TAO логов
    asyncio.create_task(collect_tao_logs(result))
    
    return user_response