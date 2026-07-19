import logging
import os

# Логгер для работы телеграм бота
bot_logger = logging.getLogger('bot_logs')
bot_logger.setLevel(logging.INFO)
bot_logger.handlers.clear()
bot_logger.propagate = False

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
    logging.Formatter('%(levelname)s | %(message)s')
)
bot_logger.addHandler(handler)