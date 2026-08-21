import logging
import sys
from pathlib import Path
from typing import Optional, Union

from loguru import logger as loguru_logger

LOG_SIM_LEVEL = "INFO"  # Simulation engine
LOG_MODEL_LEVEL = "INFO"  # ML model wrapper
LOG_RUNNER_LEVEL = "INFO"  # Experiment runner

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_LOG_DIR = PROJECT_ROOT / "workspace" / "logs"
_APP_LOG_FILE = _LOG_DIR / "app.log"
_ERROR_LOG_FILE = _LOG_DIR / "error.log"
_ENABLE_FILE_LOGGING = True

_CONFIGURED = False


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _ensure_configured():
    global _CONFIGURED
    if _CONFIGURED:
        return

    loguru_logger.remove()

    loguru_logger.add(
        sys.stdout,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    if _ENABLE_FILE_LOGGING:
        _APP_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        loguru_logger.add(
            _APP_LOG_FILE,
            rotation="00:00",
            retention="7 days",
            level="INFO",
            encoding="utf-8",
            enqueue=True,
            delay=False,
        )
        loguru_logger.add(
            _ERROR_LOG_FILE,
            rotation="00:00",
            retention="7 days",
            level="WARNING",
            encoding="utf-8",
            enqueue=True,
            delay=False,
        )

    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        log = logging.getLogger(logger_name)
        log.handlers = [InterceptHandler()]
        log.propagate = False

        # Suppress uvicorn.access logs unless explicitly enabled
        if logger_name == "uvicorn.access":
            log.setLevel(logging.WARNING)

    _CONFIGURED = True


def configure_logging(
    output_path_or_file: Union[str, Path] = None,
    enable_file_logging: bool = True,
    log_filename: str = "framework.log",
) -> None:
    global _APP_LOG_FILE, _ERROR_LOG_FILE, _ENABLE_FILE_LOGGING, _CONFIGURED
    _ENABLE_FILE_LOGGING = bool(enable_file_logging)
    if output_path_or_file:
        base = Path(output_path_or_file)
        if base.suffix:
            _APP_LOG_FILE = base
            _ERROR_LOG_FILE = base.with_name(f"{base.stem}.error{base.suffix}")
        else:
            _APP_LOG_FILE = base / log_filename
            _ERROR_LOG_FILE = base / "error.log"
    _CONFIGURED = False
    _ensure_configured()


def get_logger(
    name: str, level: str = "INFO", formatter: Optional[str] = None
) -> logging.Logger:
    _ensure_configured()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not any(isinstance(h, InterceptHandler) for h in logger.handlers):
        logger.handlers.clear()
        logger.addHandler(InterceptHandler())
    logger.propagate = False

    return logger


class Logger:
    def getLogger(
        self, name: str, level: str = "INFO", formatter: Optional[str] = None
    ) -> logging.Logger:
        return get_logger(name=name, level=level, formatter=formatter)
