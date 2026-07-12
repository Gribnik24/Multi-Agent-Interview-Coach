from langchain_openrouter import ChatOpenRouter
from langchain_core.messages import SystemMessage

from agents.agents_state import InterviewState
from config.settings import settings

llm = ChatOpenRouter(
    model=settings.SUMMARIZER_MODEL_NAME,
    api_base=settings.SUMMARIZER_MODEL_API_BASE,
    api_key=settings.SUMMARIZER_MODEL_API_KEY,
    temperature=settings.TEMPERATURE,
)

def make_summarizer_node(system_prompt: str, tools_list: list):
    
    llm_with_tools = llm.bind_tools(tools_list, parallel_tool_calls=True)
    
    def summarizer_node(state: InterviewState) -> dict:
        messages = [SystemMessage(content=system_prompt)] + state['messages']
        response = llm_with_tools.invoke(messages)
        
        return {
            'messages': [response],
            'interview_status': 'finished',
        }
    
    return summarizer_node