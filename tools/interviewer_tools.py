import sqlite3
import random
import json
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter

from agents import tao_logger
from config.settings import settings, DB_PATH


# Модель кандидата
class PartialCandidateProfile(BaseModel):
    candidate_name: Optional[str] = Field(None, description="Имя кандидата, если найдено")
    candidate_grade: Optional[str] = Field(None, description="Грейд, если найден")
    candidate_position: Optional[str] = Field(None, description="Желаемая должность, если найдена")
    questions_themes: Optional[List[str]] = Field(None, description="Список ключевых тем/технологий из ответа")


@tool
def extract_candidate_info(text: str) -> str:
    """
    Извлекает информацию о кандидате из текста (NER).
    Возвращает JSON-строку с полями candidate_name, candidate_grade,
    candidate_position, questions_themes. Ненайденные поля отсутствуют.
    """
    tao_logger.info(f'[Tool] extract_candidate_info: запуск NER-парсинга')
    prompt = f"""
    Ты — система извлечения данных. Проанализируй текст сообщения кандидата:
    "{text}"

    Верни JSON объект, соответствующий структуре данных.
    Структура:
    - candidate_name: Имя (строка при наличии)
    - candidate_grade: Грейд (строка при наличии)
    - candidate_position: Должность (строка при наличии)
    - questions_themes: Список тем (массив строк при наличии)
    
    Поля могут быть написаны в разных форматах, формах и на разных языках.
    Если поле встретилось в какой-то из форм, то в JSON отрази ближайший вид к форме из списка доступных.
    Доступные грейды: {', '.join(settings.AVAILABLE_GRADES)}
    Доступные категории вопросов: {', '.join(settings.QUESTIONS_THEMES)}
    Если поле не найдено в тексте, не указывай его.
    """
    
    response = ChatOpenRouter(
        model=settings.INTERVIEWER_MODEL_NAME,
        base_url=settings.INTERVIEWER_MODEL_API_BASE,
        api_key=settings.INTERVIEWER_MODEL_API_KEY,
        temperature=0
        ).invoke(prompt)
    
    content = response.content.strip()
    
    # Обработка случая, если был возвращен json в формате кода
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    
    # Заполнение данными      
    try:
        result = PartialCandidateProfile.model_validate_json(content)
        tao_logger.info(
            f'[Tool] extract_candidate_info: успешно извлечено — '
            f'name="{result.candidate_name}", grade="{result.candidate_grade}", '
            f'position="{result.candidate_position}", themes={result.questions_themes}'
        )
        return result.model_dump_json()
    except Exception as e:
        tao_logger.error(f'[Tool] extract_candidate_info: ошибка парсинга JSON: {e}')
        return PartialCandidateProfile().model_dump_json()


@tool
def get_question_from_db(categories: list[str], used_ids: list[int]) -> dict:
    """
    Инструмент для получения случайного основного вопроса из базы данных вопросов.
    Args:
        categories: Список категорий из которых можно задать вопрос
        used_ids: Список ID вопросов, которые уже были заданы
    Returns:
        Строка в формате JSON с полями:
            `id`: Содержит id вопроса. В случае ошибки выполнения инструмента или отсутствия незаданных вопросов на данную тему примет значение None
            `body`: Текст вопроса в случае `status == success` или содержание ошибки в случае `status == error`
    """
    tao_logger.info(f'[Tool] get_question_from_db: categories={categories}, used_ids={used_ids}')
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor() 
    except Exception as e:
        tao_logger.error(f'[Tool] get_question_from_db: ошибка подключения к БД: {e}')
        return json.dumps({'id': None, 'body': 'Ошибка подключения к базе данных'})
    
    try:
        categories_placeholders = ','.join(['?'] * len(categories))
        if not used_ids:
            query = f'SELECT id, question FROM questions WHERE [type] in ({categories_placeholders})'
            params = categories
        else:
            ids_placeholders = ','.join(['?'] * len(used_ids))
            query = f'SELECT id, question FROM questions WHERE [type] in ({categories_placeholders}) AND id NOT IN ({ids_placeholders})'
            params = categories + used_ids
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
    except Exception as e:
        tao_logger.error(f'[Tool] get_question_from_db: ошибка SQL запроса: {e}')
        return json.dumps({'id': None, 'body': 'Ошибка выполнения SQL запроса'})
        
    if not rows:
        tao_logger.info('[Tool] get_question_from_db: незаданные вопросы в категории отсутствуют')
        return json.dumps({'id': None, 'body': 'Незаданные вопросы в данной категории отсутствуют.'})
        
    q_id, question = random.choice(rows)
    tao_logger.info(f'[Tool] get_question_from_db: выбран вопрос id={q_id}')
    
    return json.dumps({'id': q_id, 'body': question}, ensure_ascii=False)


interviewer_tools_list = [extract_candidate_info, get_question_from_db]