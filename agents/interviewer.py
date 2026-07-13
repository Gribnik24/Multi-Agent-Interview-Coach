from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage

from tools.interviewer_tools import get_question_from_db
from agents.agents_state import InterviewState
from config.settings import settings

llm = ChatOpenRouter(
    model=settings.INTERVIEWER_MODEL_NAME,
    api_base=settings.INTERVIEWER_MODEL_API_BASE,
    api_key=settings.INTERVIEWER_MODEL_API_KEY,
    temperature=settings.TEMPERATURE,
)

def make_interviewer_node(system_prompt: str, tools_list: list):
    
    llm_with_tools = llm.bind_tools(tools_list, parallel_tool_calls=False)
    
    def interviewer_node(state: InterviewState) -> dict:
        messages = [SystemMessage(content=system_prompt)] + state['messages']
        response = llm_with_tools.invoke(messages)
        
        # Если модель решила вызвать инструмент
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            
            # Получаем аргументы для инструмента из state
            themes = state.get('questions_themes', [])
            used_ids = state.get('asked_questions_ids', [])
            
            # Вызываем инструмент посика вопроса
            tool_result = get_question_from_db.invoke(
                tool_call, 
                input={'categories': themes, 'used_ids': used_ids}
            )
            
            # Обновляем state: добавляем новый ID к списку использованных
            new_ids = list(used_ids)
            if tool_result.get('id'):
                new_ids.append(tool_result['id'])
            
            return {
                'messages': [response, tool_result],
                'asked_questions_ids': new_ids,
                'interview_status': state.get('interview_status', 'active')
            }
            
        return {'messages': [response], 'interview_status': state.get('interview_status', 'active')}
    
    return interviewer_node