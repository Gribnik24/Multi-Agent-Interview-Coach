import sqlite3
import random
import json
from langchain_core.tools import tool

DB_PATH = "questions.db"

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
    # Выполняем подключение к базе данных
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor() 
    except Exception as e:
        return json.dumps({'id': None, 'body': 'Ошибка подключения к базе данных'})
    
    # Выполняем SQL запрос на получение вопроса по категории
    try:
        categories_placeholders = ','.join(['?'] * len(categories))
        # Формируем запрос, если used_ids пуст. Условие NOT IN не нужно
        if not used_ids:
            query = f'SELECT id, question FROM questions WHERE category in ({categories_placeholders})'
            params = categories
        else:
            # Формируем запрос, если used_ids не пуст. Создаем плейсхолдеры для SQL запроса по id заданных вопросов
            ids_placeholders = ','.join(['?'] * len(used_ids))
            query = f'SELECT id, question FROM questions WHERE category in ({categories_placeholders}) AND id NOT IN ({ids_placeholders})'
            params = categories + used_ids
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
    except Exception as e:
        return json.dumps({'id': None, 'body': 'Ошибка выполнения SQL запроса'})
        
    # Сценарий отсутствия подходящих вопросов
    if not rows:
        return json.dumps({'id': None, 'body': 'Незаданные вопросы в данной категории отсутствуют.'})
        
    # Выбираем и возвращаем случайный вопрос из доступных
    q_id, question = random.choice(rows)
    
    return json.dumps({'id': q_id, 'body': question})

interviewer_tools_list = [get_question_from_db]