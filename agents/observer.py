from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage

from agents.agents_state import InterviewState
from config.settings import settings

llm = ChatOpenRouter(
    model=settings.OBSERVER_MODEL_NAME,
    api_base=settings.OBSERVER_MODEL_API_BASE,
    api_key=settings.OBSERVER_MODEL_API_KEY,
    temperature=settings.TEMPERATURE,
)
def make_observer_node(system_prompt: str, tools_list: list):

    llm_with_tools = llm.bind_tools(tools_list, parallel_tool_calls=True)

    def observer_node(state: InterviewState) -> dict:
        current_count = state.get('current_question_count', 0)
        stop_flag = state.get('interview_status') == 'finished'
        
        if current_count >= settings.QUESTIONS_COUNT or stop_flag:
            return {'interview_status': 'finished'}
        
        messages = [SystemMessage(content=system_prompt)] + state['messages']
        response = llm_with_tools.invoke(messages)
        
        # Observer помечает уточняющие вопросы префиксом
        is_follow_up = '[FOLLOW_UP]' in response.content
        
        return {
            'messages': [response],
            'current_question_count': current_count + (0 if is_follow_up else 1),
            'interview_status': 'active',
        }
    
    return observer_node