from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver

from typing import Optional

class InterviewState(MessagesState):
    candidate_name: Optional[str] = None # Имя кандидата
    candidate_grade: Optional[str] = None # Грейд кандидата (например: Junior)
    candidate_position: Optional[str] = None # Позиция кандидата (например: Python Developer)
    current_question_count: int = 0 # Сколько основных вопросов было задано
    interview_status: str = 'active' # Статус интервью: `active` или `finished`
    
memory = MemorySaver()   