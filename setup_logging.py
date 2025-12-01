import logging
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    info_handler = logging.FileHandler(log_dir / 'info.log')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)

    warning_handler = logging.FileHandler(log_dir / 'warning.log')
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(info_handler)
    root_logger.addHandler(warning_handler)
