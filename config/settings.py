import pandas as pd
import sqlite3
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings

DB_PATH = 'interview_questions_db/questions.db'
conn = sqlite3.connect(DB_PATH)
questions_themes = pd.read_sql(sql='SELECT DISTINCT type FROM questions;', con=conn)['type'].to_list()

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(title='Токен бота в Телеграме')
    
    # Agents-LLMs
    INTERVIEWER_MODEL_NAME: str = Field(title='Название модели-интервьюера')
    INTERVIEWER_MODEL_API_BASE: str = Field(title='API источника модели-интервьюера')
    INTERVIEWER_MODEL_API_KEY: str = Field(title='API ключ для обращения к модели-интервьюера')
    
    OBSERVER_MODEL_NAME: str = Field(title='Название модели-наблюдателя')
    OBSERVER_MODEL_API_BASE: str = Field(title='API источника модели-наблюдателя')
    OBSERVER_MODEL_API_KEY: str = Field(title='API ключ для обращения к модели-наблюдателя')
    
    TEMPERATURE: float = Field(default=0.3, title='Температура модели')
    
    # Параметры интервью
    QUESTIONS_COUNT: int = Field(default=3, title='Максимальное количество вопросов в интервью')
    QUESTIONS_THEMES: List[str] = Field(default=questions_themes, title='Доступные темы вопросов')
    
    # Параметры кандидата
    AVAILABLE_GRADES: List[str] = Field(default=['Junior', 'Middle', 'Senior', 'Team lead'], title='Доступные грейды кандидата')
    
    class Config:
        env_file = '.env'
        
settings = Settings()