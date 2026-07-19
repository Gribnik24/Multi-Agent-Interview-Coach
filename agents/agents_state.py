from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver

from typing import Optional, List, Dict

class InterviewState(MessagesState):
    # Данные кандидата
    candidate_name: Optional[str] = None # Имя кандидата
    candidate_grade: Optional[str] = None # Грейд кандидата (например: Junior)
    candidate_position: Optional[str] = None # Позиция кандидата (например: Python Developer)
    questions_themes: list[str] = [] # Темы для вопросов
    
    # Данные интервью
    asked_questions_ids: list[str] = [] # Список заданных вопросов
    current_question_count: int = 0 # Сколько основных вопросов было задано
    interview_status: str = 'active' # Статус интервью: `active` или `finished`
    
    # Лог ответов
    answers_log: List[Dict] = []
    
    # Внутренняя команда от Observer к Interviewer
    next_interviewer_instruction: Optional[str] = None

memory = MemorySaver()   