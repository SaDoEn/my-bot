import logging
import sys
import os


def setup_logger(name: str = "TranscriptionBot", level: int = logging.INFO) -> logging.Logger:
    """
    Налаштування логгера для хмарного хостингу

    Args:
        name (str): Ім'я логгера
        level (int): Рівень логування

    Returns:
        logging.Logger: Налаштований логгер
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if os.getenv('ENVIRONMENT') == 'local':
        try:
            os.makedirs('logs', exist_ok=True)
            from datetime import datetime

            file_handler = logging.FileHandler(
                f'logs/bot_{datetime.now().strftime("%Y%m%d")}.log',
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        except Exception as e:
            logger.warning(f"Не вдалося створити файловий логгер: {e}")

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return logger