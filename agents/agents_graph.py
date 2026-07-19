from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

from agents import tao_logger
from agents.agents_state import InterviewState, memory
from agents.observer import make_observer_node
from agents.interviewer import make_interviewer_node

from tools.observer_tools import observer_tools_list
from tools.interviewer_tools import interviewer_tools_list

from config.system_prompts import OBSERVER_SYSTEM_PROMPT, INTERVIEWER_SYSTEM_PROMPT


def start_router(state: InterviewState) -> str:
    """
    Маршрутизация из START.
    Решает, кто должен обработать очередное сообщение пользователя:
    - /stop -> observer (формирование отчёта)
    - Профиль неполный -> interviewer (сбор данных)
    - Профиль полный + ответ кандидата -> observer (оценка ответа)
    - Иначе -> interviewer
    """
    messages = state.get('messages', [])
    last_message = messages[-1] if messages else None

    # Обработка команды /stop - завершаем интервью и идём к Observer за отчётом
    if (
        isinstance(last_message, HumanMessage)
        and isinstance(last_message.content, str)
        and last_message.content.strip().lower() == '/stop'
    ):
        tao_logger.info('[Routing] START -> observer (команда /stop, формирование отчёта)')
        return 'observer'

    # Если профиль кандидата ещё не собран - Interviewer продолжает сбор данных
    profile_complete = (
        state.get('candidate_name')
        and state.get('candidate_position')
        and state.get('candidate_grade')
    )
    if not profile_complete:
        tao_logger.info('[Routing] START -> interviewer (профиль неполный, сбор данных)')
        return 'interviewer'

    # Профиль полон и пришло сообщение от пользователя - Observer оценивает ответ
    if isinstance(last_message, HumanMessage):
        tao_logger.info('[Routing] START -> observer (ответ кандидата, оценка)')
        return 'observer'

    # По умолчанию - Interviewer
    tao_logger.info('[Routing] START -> interviewer (по умолчанию)')
    return 'interviewer'


def observer_paths(state: InterviewState) -> str:
    """
    Варианты действий агента-оценщика (Observer)
    """
    last_message = state['messages'][-1]
    
    # Вызов инструмента при необходимости
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tao_logger.info('[Routing] Observer -> observer_tools (вызов инструмента)')
        return 'observer_tools'
    
    # Если интервью завершено
    if state.get('interview_status') == 'finished':
        tao_logger.info('[Routing] Observer -> END (интервью завершено)')
        return END
    
    # Иначе передача команды Interviewer'у
    tao_logger.info('[Routing] Observer -> interviewer (передача инструкции)')
    return 'interviewer'


def interviewer_paths(state: InterviewState) -> str:
    """
    Маршрутизация Interviewer'а:
    - Вызов инструмента -> interviewer_tools
    - Иначе -> END (вопрос/уточнение сформированы для пользователя)
    """
    last_message = state['messages'][-1]
    
    # Вызов инструмента при необходимости
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tao_logger.info('[Routing] Interviewer -> interviewer_tools (вызов инструмента)')
        return 'interviewer_tools'
    
    # Вопрос/уточнение сформированы - отдаём пользователю
    tao_logger.info('[Routing] Interviewer -> END (завершение)')
    return END


def workflow_builder():
    """
    Граф мультиагентной системы
    """
    tao_logger.info('Построение графа мультиагентной системы (workflow_builder)')
    
    workflow = StateGraph(InterviewState)
    
    # Узлы агентов
    workflow.add_node('observer', make_observer_node(OBSERVER_SYSTEM_PROMPT, observer_tools_list))
    workflow.add_node('interviewer', make_interviewer_node(INTERVIEWER_SYSTEM_PROMPT, interviewer_tools_list))
    
    # Узлы инструментов
    workflow.add_node('observer_tools', ToolNode(observer_tools_list))
    workflow.add_node('interviewer_tools', ToolNode(interviewer_tools_list))
    
    # Связи графа
    workflow.add_conditional_edges(START, start_router)
    workflow.add_conditional_edges('observer', observer_paths)
    workflow.add_conditional_edges('interviewer', interviewer_paths)
    workflow.add_edge('observer_tools', 'observer')
    workflow.add_edge('interviewer_tools', 'interviewer')

    tao_logger.info('Граф мультиагентной системы успешно построен и скомпилирован')
    return workflow.compile(checkpointer=memory)


multi_agent_system = workflow_builder()