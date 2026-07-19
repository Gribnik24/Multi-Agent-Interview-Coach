from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, ToolMessage

from agents import tao_logger
from agents.agents_state import InterviewState, memory
from agents.observer import make_observer_node
from agents.interviewer import make_interviewer_node

from tools.observer_tools import observer_tools_list
from tools.interviewer_tools import interviewer_tools_list

from config.system_prompts import OBSERVER_SYSTEM_PROMPT, INTERVIEWER_SYSTEM_PROMPT


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
    - Есть инструкция от Observer'а -> observer
    - Ответ пользователя (HumanMessage) -> observer (оценка ответа)
    - Конец
    """
    last_message = state['messages'][-1]
    
    # Вызов инструмента при необходимости
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        tao_logger.info('[Routing] Interviewer -> interviewer_tools (вызов инструмента)')
        return 'interviewer_tools'
    
    # Если есть инструкция от Observer'а (например, "оцени профиль" или "задай следующий вопрос")
    if state.get('next_interviewer_instruction'):
        tao_logger.info('[Routing] Interviewer -> observer (есть инструкция от Observer)')
        return 'observer'
    
    # Если последнее сообщение - ответ пользователя, передаём ответ кандидата Observer'у для оценки.
    if isinstance(last_message, HumanMessage):
        tao_logger.info('[Routing] Interviewer -> observer (ответ пользователя, передача на оценку)')
        return 'observer'

    # Если последнее сообщение - работа инструмента, передаём результат инструмента.
    if isinstance(last_message, ToolMessage):
        tao_logger.info('[Routing] Interviewer -> observer (результат инструмента, передача на оценку)')
        return 'observer'
    
    # По умолчанию конец
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
    workflow.add_edge(START, 'interviewer')
    
    workflow.add_conditional_edges('observer', observer_paths)
    workflow.add_conditional_edges('interviewer', interviewer_paths)
    workflow.add_edge('observer_tools', 'observer')
    workflow.add_edge('interviewer_tools', 'interviewer')

    tao_logger.info('Граф мультиагентной системы успешно построен и скомпилирован')
    return workflow.compile(checkpointer=memory)


multi_agent_system = workflow_builder()