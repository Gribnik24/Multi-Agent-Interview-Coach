import json

from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage

from agents import tao_logger
from agents.agents_state import InterviewState
from config.settings import settings
from tools.observer_tools import evaluate_profile_answer, evaluate_interview_answer, generate_report

llm = ChatOpenRouter(
    model=settings.OBSERVER_MODEL_NAME,
    base_url=settings.OBSERVER_MODEL_API_BASE,
    api_key=settings.OBSERVER_MODEL_API_KEY,
    temperature=settings.TEMPERATURE,
)


def _handle_report_generation(state: InterviewState, messages: list, llm_with_tools: ChatOpenRouter) -> dict:
    """
    Формирует финальный отчёт по результатам интервью.
    Вызывается когда interview_status == 'finished'.
    """
    answers_log = state.get('answers_log', [])
    candidate_name = state.get('candidate_name')
    candidate_grade = state.get('candidate_grade')
    candidate_position = state.get('candidate_position')
    
    tao_logger.info('[Observer] Старт формирования финального отчёта')
    
    # Формируем промпт с контекстом отчёта
    extended_prompt = messages[0].content + f"""

ФОРМИРУЙ ФИНАЛЬНЫЙ ОТЧЁТ:
- Кандидат: {candidate_name}, {candidate_position}, {candidate_grade}
- Ответы кандидата: {json.dumps(answers_log, ensure_ascii=False)}

ВЫЗОВИ инструмент generate_report с этими данными.
"""
    
    new_messages = [SystemMessage(content=extended_prompt)] + state['messages']
    response = llm_with_tools.invoke(new_messages)
    
    if response.tool_calls:
        tool_name = response.tool_calls[0].get('name', '')
        tool_args = response.tool_calls[0].get('args', {})
        tao_logger.info(f'[Observer] Вызван инструмент: {tool_name} с аргументами: {tool_args}')
        tao_logger.info(f'[Observer] Финальный отчёт по результатам интервью успешно сформирован')
        return {
            'messages': [response],
            'interview_status': 'finished',
            'next_interviewer_instruction': None
        }
    
    # Fallback: если LLM не вызвал инструмент
    tao_logger.warning('[Observer] LLM не вызвал инструмент generate_report, формируем отчёт вручную')
    return {
        'messages': [AIMessage(content="[Observer]: Интервью завершено. Ошибка при генерации отчёта.")],
        'interview_status': 'finished'
    }


def _handle_profile_assessment(state: InterviewState, messages: list, llm_with_tools: ChatOpenRouter) -> dict:
    """
    Оценивает заполненность профиля кандидата.
    Если что-то не хватает — даёт команду Interviewer'у спросить.
    Если профиль полон — передаёт управление Interviewer'у для начала собеседования.
    """
    tao_logger.info(f'[Observer] Старт проверки заполненности профиля')
    
    # Формируем промпт с текущим профилем
    extended_prompt = messages[0].content + f"""

Текущий профиль кандидата:
- Имя: {state.get('candidate_name', 'не указано')}
- Грейд: {state.get('candidate_grade', 'не указано')}
- Позиция: {state.get('candidate_position', 'не указано')}
- Темы: {', '.join(state.get('questions_themes', []))}

Оцени заполненность профиля.
ВЫЗОВИ инструмент evaluate_profile_answer.
"""
    
    new_messages = [SystemMessage(content=extended_prompt)] + state['messages']
    response = llm_with_tools.invoke(new_messages)
    
    if response.tool_calls:
        tool_name = response.tool_calls[0].get('name', '')
        tool_args = response.tool_calls[0].get('args', {})
        tao_logger.info(f'[Observer] Вызван инструмент: {tool_name} с аргументами: {tool_args}')
        
        return {
            'messages': [response],
            'interview_status': 'active',
            'next_interviewer_instruction': None
        }
    
    # Fallback: если LLM не вызвал инструмент
    tao_logger.warning('[Observer] LLM не вызвал инструмент evaluate_profile_answer')
    
    missing = []
    if not state.get('candidate_name'):
        missing.append('имя')
    if not state.get('candidate_grade'):
        missing.append('грейд')
    if not state.get('candidate_position'):
        missing.append('должность')
    
    thought = f"[Observer]: Профиль кандидата. Пропущено: {', '.join(missing) if missing else '-'}."
    
    if missing:
        instruction = f"Собери данные профиля. Пользователю не хватает: {', '.join(missing)}. Спроси об этом."
        tao_logger.info(f'[Observer] Проверка заполненности профиля успешно завершена. Формирование команды Interviewer: сбор недостающих данных профиля')
    else:
        instruction = "Собеседование началось. ЗАДАЙ ПЕРВЫЙ ВОПРОС: используй инструмент get_question_from_db для получения вопроса из базы. Категории: questions_themes."
        tao_logger.info('[Observer] Профиль полон. Формирование команды Interviewer: начать собеседование')
    
    return {
        'messages': [AIMessage(content=thought)],
        'interview_status': 'active',
        'next_interviewer_instruction': instruction
    }


def _handle_interview_response(state: InterviewState, messages: list, llm_with_tools: ChatOpenRouter) -> dict:
    """
    Оценивает ответ кандидата на вопрос собеседования.
    - Если follow_up: обновляем последнюю запись в answers_log (score в "копилку").
    - Если next_question: добавляем новую запись в answers_log.
    - Если finish: помечаем интервью как завершённое.
    """
    tao_logger.info('Старт оценки ответа кандидата')
    
    # Находим последний вопрос (AIMessage) и ответ (HumanMessage)
    last_human = None
    last_ai = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_human = msg
        elif isinstance(msg, AIMessage) and last_human:
            last_ai = msg
            break
    
    # Нет вопроса/ответа — просто передаём управление Interviewer'у
    if not last_ai or not last_human:
        tao_logger.warning('[Observer] Оценка ответа кандидата завершилась с ошибкой: нет пары вопрос/ответ. Передача управления Interviewer')
        return {
            'messages': [AIMessage(content="[Observer]: Жду вопрос и ответ от Interviewer'а.")],
            'interview_status': state.get('interview_status', 'active'),
            'next_interviewer_instruction': None
        }
    
    # Формируем промпт с вопросом и ответом кандидата
    extended_prompt = messages[0].content + f"""

ОЦЕНИ ОТВЕТ КАНДИДАТА:
Вопрос: {last_ai.content}
Ответ: {last_human.content}

ВЫЗОВИ инструмент evaluate_interview_answer с этими данными.
"""
    
    new_messages = [SystemMessage(content=extended_prompt)] + state['messages']
    response = llm_with_tools.invoke(new_messages)
    
    if response.tool_calls:
        tool_name = response.tool_calls[0].get('name', '')
        tool_args = response.tool_calls[0].get('args', {})
        tao_logger.info(f'[Observer] Вызван инструмент: {tool_name} с аргументами: {tool_args}')
        tao_logger.info('[Observer] Оценка ответа кандидата завершилась успешно')
        
        return {
            'messages': [response],
            'interview_status': state.get('interview_status', 'active'),
            'next_interviewer_instruction': None
        }
    
    # Fallback: если LLM не вызвал инструмент
    tao_logger.warning('[Observer] Оценка ответа кандидата завершилась с ошибкой: LLM не вызвал инструмент evaluate_interview_answer')
    
    thought = (
        f"[Observer]: Вопрос: {last_ai.content[:80]}...\n"
        f"Ответ: {last_human.content[:80]}...\n"
        f"Ошибка оценки ответа кандидата."
    )
    
    return {
        'messages': [AIMessage(content=thought)],
        'interview_status': state.get('interview_status', 'active'),
        'next_interviewer_instruction': "Задай следующий вопрос."
    }


def make_observer_node(system_prompt: str, tools_list: list):
    llm_with_tools = llm.bind_tools(tools_list)

    def observer_node(state: InterviewState) -> dict:
        """
        Observer управляет процессом интервью:
        1. Если профиль неполный — оценивает заполненность и даёт команду Interviewer'у.
        2. Если профиль полный — оценивает ответы кандидата и решает: next / follow_up / finish.
        3. Если интервью завершено (/stop или лимит вопросов) — формирует финальный отчёт.
        """
        tao_logger.info('[Observer] Старт работы узла Observer')
        
        # Формируем messages с системным промптом
        extended_system_prompt = system_prompt
        if state.get('candidate_name') or state.get('candidate_position') or state.get('candidate_grade'):
            extended_system_prompt += f"""

Текущий профиль кандидата:
- Имя: {state.get('candidate_name', 'не указано')}
- Позиция: {state.get('candidate_position', 'не указано')}
- Грейд: {state.get('candidate_grade', 'не указано')}
- Темы: {', '.join(state.get('questions_themes', []))}
"""
        
        messages = [SystemMessage(content=extended_system_prompt)] + state['messages']
        
        # Формирование финального отчета по кандидату
        if state.get('interview_status') == 'finished':
            return _handle_report_generation(state, messages, llm_with_tools)
        
        # Проверка заполненности профиля
        profile_complete = (
            state.get("candidate_name") 
            and state.get("candidate_position") 
            and state.get("candidate_grade")
        )
        
        # Запрос на дозаполнения профиля
        if not profile_complete:
            return _handle_profile_assessment(state, messages, llm_with_tools)
        
        # Оценка ответа кандидата
        return _handle_interview_response(state, messages, llm_with_tools)

    return observer_node