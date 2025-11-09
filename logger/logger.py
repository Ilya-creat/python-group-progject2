import logging
import os

from logging.handlers import RotatingFileHandler

from settings import logging_set_level

_loggers = {}

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging_level = {
    "10": logging.DEBUG,
    "20": logging.INFO,
    "30": logging.WARNING,
    "40": logging.ERROR,
    "50": logging.CRITICAL
}


def get_logger(file_path: str) -> logging.Logger:
    """
    Возвращает уникальный экземпляр logger для каждого модуля.
    Пример использования: get_logger(__file__)

    :param file_path: путь к скрипту, который необходимо логировать
    """

    name = os.path.splitext(os.path.basename(file_path))[0]
    log_path = os.path.join(LOG_DIR, f"{name}.log")

    if _loggers.get(name):
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging_level[logging_set_level])

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s] [%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_path, maxBytes=8388608, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.propagate = False

    _loggers[name] = logger
    return logger
