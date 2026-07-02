from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(title='Токен бота в Телеграме')
    
    # LLMs
    INTERVIEWER_MODEL_NAME: str = Field(title='Название модели-интервьюера')
    INTERVIEWER_MODEL_API_BASE: str = Field(title='API источника модели-интервьюера')
    INTERVIEWER_MODEL_API_KEY: str = Field(title='API ключ для обращения к модели-интервьюера')
    
    OBSERVER_MODEL_NAME: str = Field(title='Название модели-наблюдателя')
    OBSERVER_MODEL_API_BASE: str = Field(title='API источника модели-наблюдателя')
    OBSERVER_MODEL_API_KEY: str = Field(title='API ключ для обращения к модели-наблюдателя')
    
    SUMMARIZER_MODEL_NAME: str = Field(title='Название модели-фидбэкера')
    SUMMARIZER_MODEL_API_BASE: str = Field(title='API источника модели-фидбэкера')
    SUMMARIZER_MODEL_API_KEY: str = Field(title='API ключ для обращения к модели-фидбэкера')
    
    TEMPERATURE: float = Field(default=0.3, title='Температура модели')
    
    # Интервью
    QUESTIONS_COUNT: int = Field(default=3, title='Максимальное количество вопросов в интервью')
    
    class Config:
        env_file = '.env'
        
settings = Settings()