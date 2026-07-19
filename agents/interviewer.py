import json
from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage, ToolMessage

from agents import tao_logger
from agents.agents_state import InterviewState
from config.settings import settings

llm = ChatOpenRouter(
    model=settings.INTERVIEWER_MODEL_NAME,
    base_url=settings.INTERVIEWER_MODEL_API_BASE,
    api_key=settings.INTERVIEWER_MODEL_API_KEY,
    temperature=settings.TEMPERATURE,
)

def make_interviewer_node(system_prompt: str, tools_list: list):
    """
    Создаёт узел Interviewer.
    При получении команды от Observer начать/продолжить собеседование
    принудительно вызывает инструмент get_question_from_db (tool_choice).
    В остальных случаях (сбор данных, follow_up) — работает через LLM как обычно.
    """
    def _get_llm_with_forced_tool():
        """Возвращает LLM с принудительным вызовом get_question_from_db."""
        return llm.bind_tools([t for t in tools_list if t.name == 'get_question_from_db'],
                              tool_choice='get_question_from_db',
                              parallel_tool_calls=False
                              )
    
    def interviewer_node(state: InterviewState) -> dict:
        tao_logger.info('[Interviewer] Старт работы узла Interviewer')

        # Проверяем: есть ли команда от Observer (инструкция для следующего шага)
        instruction = state.get('next_interviewer_instruction')
        if instruction:
            tao_logger.info(f'[Interviewer] Получена инструкция от Observer: {instruction}')

        # Проверяем, был ли вызов инструмента на предыдущем шаге
        last_message = state['messages'][-1] if state['messages'] else None
        is_tool_result = isinstance(last_message, ToolMessage)

        # Обработка результата инструмента, выполненного на предыдущем шаге (если есть)
        state_updates = {}
        if is_tool_result:
            tool_name = last_message.name
            tao_logger.info(f'[Interviewer] Обработка результата инструмента: {tool_name}')

            content = last_message.content
            try:
                data = json.loads(content) if isinstance(content, str) else content
            except (json.JSONDecodeError, TypeError):
                tao_logger.error(f'[Interviewer] Не удалось распарсить JSON из результата инструмента {tool_name}')
                data = {}

            # Если `extract_candidate_info`, то обновляем профиль кандидата в state
            if tool_name == 'extract_candidate_info':
                state_updates['candidate_name'] = data.get('candidate_name')
                state_updates['candidate_grade'] = data.get('candidate_grade')
                state_updates['candidate_position'] = data.get('candidate_position')
                if data.get('questions_themes'):
                    state_updates['questions_themes'] = data['questions_themes']
                tao_logger.info(
                    f'[Interviewer] Профиль обновлён: name={data.get("candidate_name")}, '
                    f'grade={data.get("candidate_grade")}, position={data.get("candidate_position")}'
                )

            # Если `get_question_from_db`, то Вопрос из БД: добавляем ID вопроса из БД в список заданных
            elif tool_name == 'get_question_from_db':
                new_ids = list(state.get('asked_questions_ids', []))
                if data.get('id'):
                    new_ids.append(data['id'])
                state_updates['asked_questions_ids'] = new_ids
                tao_logger.info(f'[Interviewer] Вопрос добавлен в список заданных: id={data.get("id")}')

        llm_with_tools = llm.bind_tools(tools_list, parallel_tool_calls=False)
        
        # Формирование промпта с контекстом
        extended_system_prompt = system_prompt.format(
            candidate_position=state.get('candidate_position', 'Unknown'),
            candidate_grade=state.get('candidate_grade', 'Unknown'),
            questions_themes=settings.QUESTIONS_THEMES,
            questions_count=settings.QUESTIONS_COUNT
        )
        if instruction:
            extended_system_prompt = f"""{extended_system_prompt}

[Observer Instruction]: {instruction}

Следуй этой инструкции при формировании следующего сообщения.
"""

        messages = [SystemMessage(content=extended_system_prompt)] + state['messages']
        response = llm_with_tools.invoke(messages)

        # LLM вызвала инструмент 
        if response.tool_calls:
            tool_name = response.tool_calls[0].get('name', '')
            tao_logger.info(f'[Interviewer] Вызван инструмент: {tool_name}')

            return {
                'messages': [response],
                **state_updates,
                'interview_status': state.get('interview_status', 'active'),
                'next_interviewer_instruction': None
            }

        # LLM сгенерировал текст (вопрос кандидату или уточнение)
        tao_logger.info('[Interviewer] Сгенерирован текстовый ответ (вопрос/уточнение)')
        return {
            'messages': [response],
            **state_updates,
            'interview_status': state.get('interview_status', 'active'),
            'next_interviewer_instruction': None
        }
    
    return interviewer_node