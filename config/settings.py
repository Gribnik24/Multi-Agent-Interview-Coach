from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str = Field(description='Токен бота в Телеграме')
    
    # LLMs
    INTERVIEWER_MODEL_NAME: str = Field(description='Название модели-интервьюера')
    INTERVIEWER_MODEL_API_BASE: str = Field(description='API источника модели-интервьюера')
    INTERVIEWER_MODEL_API_KEY: str = Field(description='API ключ для обращения к модели-интервьюера')
    
    OBSERVER_MODEL_NAME: str = Field(description='Название модели-наблюдателя')
    OBSERVER_MODEL_API_BASE: str = Field(description='API источника модели-наблюдателя')
    OBSERVER_MODEL_API_KEY: str = Field(description='API ключ для обращения к модели-наблюдателя')
    
    SUMMARIZER_MODEL_NAME: str = Field(description='Название модели-фидбэкера')
    SUMMARIZER_MODEL_API_BASE: str = Field(description='API источника модели-фидбэкера')
    SUMMARIZER_MODEL_API_KEY: str = Field(description='API ключ для обращения к модели-фидбэкера')
    
    TEMPERATURE: float = Field(default=0.3, description='Температура модели')
    
    class Config:
        env_file = '.env'
        
settings = Settings()