import logging
import os

# Логгер для работы телеграм бота
logger = logging.getLogger('bot_logs')
logger.setLevel(logging.INFO)
logger.handlers.clear()
logger.propagate = False

# Создание папки logs/ в корне при ее отсутствии
current_dir = os.path.dirname(__file__)
log_dir = os.path.abspath(os.path.join(current_dir, '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)

# Файловый обработчик для логов бота
log_file = os.path.join(log_dir, 'bot_logs.log')
handler = logging.FileHandler(
    filename=log_file,
    mode='a',
    encoding='utf-8'
)
handler.setFormatter(
    logging.Formatter('[BOT LOGS]: %(levelname)s | %(message)s')
)
logger.addHandler(handler)