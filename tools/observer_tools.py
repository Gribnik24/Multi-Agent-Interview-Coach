import json
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openrouter import ChatOpenRouter

from agents import tao_logger
from config.settings import settings


# Модель пропущенных полей кандидата
class ProfileAssessment(BaseModel):
    """Результат оценки заполненности профиля кандидата."""
    missing_fields: List[str] = Field(
        description="Список незаполненных полей профиля (например: ['имя', 'должность', 'грейд']). Пусто, если профиль полон."
    )
    interview_start: bool = Field(
        description="True, если профиль полон и можно начинать собеседование."
    )

# Модель оценки ответа кандидата
class AnswerEvaluationResult(BaseModel):
    """Результат оценки ответа кандидата на вопрос собеседования."""
    score: int = Field(description="Оценка ответа от 0 до 100")
    is_correct: bool = Field(description="Фактически ли верен ответ")
    hallucination: bool = Field(description="Есть ли в ответе галлюцинации/бред")
    confidence: str = Field(description="Уверенность кандидата: high, medium, low")
    feedback: str = Field(description="Краткий фидбэк: что хорошо, а что плохо")
    follow_up_action: str = Field(
        description="Действие: 'next_question' (хороший ответ, следующий), 'follow_up' (уточнить), 'finish' (лимит/провал)"
    )

# Модель финального отчета
class ReportData(BaseModel):
    """Финальный отчёт по результатам интервью."""
    verdict: str = Field(description="Hire / No Hire / Strong Hire")
    hard_skills: str = Field(description="Оценка технических навыков по темам")
    soft_skills: str = Field(description="Оценка уверенности, честности, наличия галлюцинаций")
    roadmap: str = Field(description="Рекомендации: что подтянуть на основе логов")


@tool
def evaluate_profile_answer(
    candidate_name: Optional[str] = None,
    candidate_grade: Optional[str] = None,
    candidate_position: Optional[str] = None,
    questions_themes: Optional[List[str]] = None
) -> ProfileAssessment:
    """
    Анализирует текущие данные профиля кандидата и определяет, какие поля ещё не заполнены.
    Args:
        candidate_name: Имя кандидата (может быть None)
        candidate_grade: Грейд (может быть None)
        candidate_position: Должность (может быть None)
        questions_themes: Темы/технологии (может быть None)
    Returns:
        ProfileAssessment: класс со следующими полями:
                            missing_fileds: Список незаполненных полей профиля (например: ['имя', 'должность', 'грейд']). Пусто, если профиль полон.
                            interview_start: True, если профиль полон и можно начинать собеседование.
    """
    tao_logger.info('[Tool] evaluate_profile_answer: оценка заполненности профиля')
    
    # Заполнение полей
    missing = []
    if not candidate_name:
        missing.append("имя")
    if not candidate_position:
        missing.append("должность")
    if not candidate_grade:
        missing.append("грейд")
    if not questions_themes or len(questions_themes) == 0:
        missing.append("темы")
    start_interview_flag = True if len(missing) == 0 else False
    
    result = ProfileAssessment(
        missing_fields=missing,
        interview_start=start_interview_flag
    )
    tao_logger.info(f'[Tool] evaluate_profile_answer: missing={result.missing_fields}, interview_start={result.interview_start}')
    return result


@tool
def evaluate_interview_answer(question: str, answer: str) -> AnswerEvaluationResult:
    """
    Оценивает ответ кандидата на вопрос собеседования.
    Проверяет фактическую точность, наличие галлюцинаций, уверенность.
    Args:
        question: Текст вопроса интервьюера
        answer: Ответ кандидата
    Returns:
        AnswerEvaluationResult - оценка, фидбэк и рекомендация по действию.
    """
    tao_logger.info(f'[Tool] evaluate_interview_answer: оценка ответа (question[:50]={question[:50]}...)')
    prompt = f"""
    Ты - строгий технический интервьюер (Observer). Оцени ответ кандидата.
    
    Вопрос: "{question}"
    Ответ: "{answer}"
    
    Верни JSON объект, соответствующий структуре данных.
    Структура:
    - score: Общий балл ответа от 0 до 100
    - is_correct: Фактически ли верен ответ (True или False)
    - hallucination: Есть ли в ответе бред/галлюцинации (True или False)
    - confidence: Уверенность кандидата: 'high', 'medium', 'low'
    - feedback: Краткий фидбэк: что хорошо, а что плохо
    - follow_up_action: Возможные значения:
                        'next_question' - если ответ хороший и полный
                        'follow_up' - если ответ верный, но слишком краткий
                        'finish' - если кандидат провалился или лимит исчерпан
    """
    
    response = ChatOpenRouter(
        model=settings.OBSERVER_MODEL_NAME,
        base_url=settings.OBSERVER_MODEL_API_BASE,
        api_key=settings.OBSERVER_MODEL_API_KEY,
        temperature=0.3
        ).invoke(prompt)

    content = response.content.strip()
    
    # Обработка случая, если был возвращен json в формате кода
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    
    # Заполнение данными     
    try:
        result = AnswerEvaluationResult.model_validate_json(content)
        tao_logger.info(
            f'[Tool] evaluate_interview_answer: score={result.score}, '
            f'is_correct={result.is_correct}, action={result.follow_up_action}'
        )
        return result
    except Exception as e:
        tao_logger.error(f'[Tool] evaluate_interview_answer: ошибка парсинга JSON: {e}')
        return AnswerEvaluationResult(
            score=0, is_correct=False, hallucination=False, confidence="low",
            feedback="Ошибка анализа ответа.", follow_up_action="next_question"
        )


@tool
def generate_report(
    answers_log: List[Dict],
    candidate_name: Optional[str] = None,
    candidate_grade: Optional[str] = None,
    candidate_position: Optional[str] = None
) -> ReportData:
    """
    Формирует финальный отчёт по результатам интервью на основе логов ответов и профиля кандидата.
    Args:
        answers_log: Список всех ответов кандидата с оценками
        candidate_name: Имя кандидата
        candidate_grade: Грейд кандидата
        candidate_position: Должность кандидата
    Returns:
        ReportData - вердикт, оценка hard/soft skills, roadmap для развития.
        ReportData: класс со следующими полями:
                    verdict: Конечный вердикт. Принимает поля 'Strong Hire' (отлично), 'Hire' (хорошо), 'No Hire' (провал)
                    hard_skills: Описание оценки технических знаний по темам
                    soft_skills: Оценка уверенности, честности, наличия галлюцинаций
                    roadmap: Конкретные рекомендации по развитию на основе слабых мест
    """
    tao_logger.info(f'[Tool] generate_report: формирование отчёта ({len(answers_log)} ответов)')
    prompt = f"""
    Ты - Senior Tech Recruiter. Сформируй финальный отчёт по результатам технического интервью.
    
    Профиль кандидата:
    - Имя: {candidate_name or 'Не указано'}
    - Грейд: {candidate_grade or 'Не указан'}
    - Позиция: {candidate_position or 'Не указана'}
    
    Логи ответов ({len(answers_log)} вопросов):
    {json.dumps(answers_log, indent=2, ensure_ascii=False)}
    
    Верни JSON объект, соответствующий структуре данных.
    Структура:
    - verdict: 'Strong Hire' (отлично), 'Hire' (хорошо), 'No Hire' (провал)
    - hard_skills: Описание оценки технических знаний по темам
    - soft_skills: Оценка уверенности, честности, наличия галлюцинаций
    - roadmap: Конкретные рекомендации по развитию на основе слабых мест
    """
    
    response = ChatOpenRouter(
        model=settings.OBSERVER_MODEL_NAME,
        base_url=settings.OBSERVER_MODEL_API_BASE,
        api_key=settings.OBSERVER_MODEL_API_KEY,
        temperature=0.4
        ).invoke(prompt)

    content = response.content.strip()
    
    # Обработка случая, если был возвращен json в формате кода
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]

    # Заполнение данными 
    try:
        result = ReportData.model_validate_json(content)
        tao_logger.info(f'[Tool] generate_report: отчёт сформирован, verdict={result.verdict}')
        return result
    except Exception as e:
        tao_logger.error(f'[Tool] generate_report: ошибка парсинга JSON: {e}')
        return ReportData(
            verdict="Hire",
            hard_skills="Информация недостаточна для детальной оценки.",
            soft_skills="Не удалось проанализировать.",
            roadmap="Рекомендуем провести дополнительное собеседование."
        )


observer_tools_list = [evaluate_profile_answer, evaluate_interview_answer, generate_report]