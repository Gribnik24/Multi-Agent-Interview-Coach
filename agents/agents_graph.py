from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agents.agents_state import InterviewState, memory
from agents.observer import observer_node
from agents.interviewer import interviewer_node
from agents.summarizer import summarizer_node

from tools.observer_tools import observer_tools_list
from tools.interviewer_tools import interviewer_tools_list
from tools.summarizer_tools import summarizer_tools_list

from config.settings import settings

def observer_paths(state: InterviewState) -> str:
    """
    Варианты действий агента-оценщика
    """
    last_message = state["messages"][-1]
    
    # Вызов инструмента при необходимости
    need_tool_call = hasattr(last_message, 'tool_calls') and last_message.tool_calls
    if need_tool_call:
        return 'observer_tools'
    
    # Вызов агента-фидбэкера
    # Если поступила команда /stop
    stop_command_flag = state.get("interview_status") == "finished"
    # Если достигнуто максимальное количество основных вопросов
    max_questions_flag = state.get("current_question_count", 0) >= settings.QUESTIONS_COUNT
    if stop_command_flag or max_questions_flag:
        return 'summarizer'
    
    # Иначе передача информации агенту-интервьюеру
    return 'interviewer'

def interviewer_paths(state: InterviewState) -> str:
    """
    Варианты действий агента-интервьюера
    """
    last_message = state["messages"][-1]
    
    # Вызов инструмента при необходимости
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "interviewer_tools"
    
    # Завершение работы графа
    return END

def summarizer_paths(state: InterviewState) -> str:
    """
    Варианты действий агента-фидбэкера
    """
    last_message = state["messages"][-1]
    
    # Вызов инструмента при необходимости
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "summarizer_tools"
    
    # Завершение работы графа
    return END

def workflow_builder():
    """
    Граф мультиагентной системы
    """
    workflow = StateGraph(InterviewState)
    
    # Ячейки агентов
    workflow.add_node('observer', observer_node)
    workflow.add_node('interviewer', interviewer_node)
    workflow.add_node('summarizer', summarizer_node)
    
    # Ячейки инструментов
    workflow.add_node('observer_tools', ToolNode(observer_tools_list))
    workflow.add_node('interviewer_tools', ToolNode(interviewer_tools_list))
    workflow.add_node('summarizer_tools', ToolNode(summarizer_tools_list))
    
    # Связи агентов
    workflow.add_edge(START, 'observer')
    workflow.add_conditional_edges('observer', observer_paths)
    workflow.add_conditional_edges('interviewer', interviewer_paths)
    workflow.add_conditional_edges('summarizer', summarizer_paths)
    workflow.add_edge('observer_tools', 'observer')
    workflow.add_edge('interviewer_tools', 'interviewer')
    workflow.add_edge('summarizer_tools', 'summarizer')

    return workflow.compile(checkpointer=memory)

multi_agent_system = workflow_builder()