import logging
from logging import Formatter, StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    formatter = Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    info_handler = RotatingFileHandler(
        log_dir / 'info.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=10,
        encoding='utf-8',
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    root_logger.addHandler(info_handler)

    warning_handler = RotatingFileHandler(
        log_dir / 'warning.log',
        maxBytes=1024*1024,  # 1MB
        backupCount=10,
        encoding='utf-8',
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)
    root_logger.addHandler(warning_handler)
