import logging
import os

# Автоматическое логирование в модулях telegram/handlers
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()

# Создание папки logs/ в корне при ее отсутствии
current_dir = os.path.dirname(__file__)
log_dir = os.path.abspath(os.path.join(current_dir, '..', 'logs'))
os.makedirs(log_dir, exist_ok=True)

# Формат логов
log_file = os.path.join(log_dir, 'logs.log')
handler = logging.FileHandler(filename=log_file,
                              mode="a",
                              encoding='utf-8'
                              )
handler.setFormatter(
    logging.Formatter('%(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(handler)