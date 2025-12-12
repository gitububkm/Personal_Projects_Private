"""
Интеграция с Hawk для трекинга ошибок
"""
import os
import structlog
from typing import Optional, Any

logger = structlog.get_logger()

# Инициализация Hawk (если доступен)
hawk_client = None
HAWK_TOKEN = os.getenv("HAWK_TOKEN", "")

try:
    if HAWK_TOKEN and HAWK_TOKEN != "your_hawk_token_here":
        try:
            from hawk_python_sdk import Hawk
            hawk_client = Hawk(HAWK_TOKEN)
            logger.info("Hawk initialized")
        except ImportError:
            logger.warning("hawk_not_installed", message="Install hawk-python-sdk package to enable error tracking")
            hawk_client = None
    else:
        logger.info("hawk_disabled", reason="not_configured")
        hawk_client = None
except Exception as e:
    logger.error("hawk_init_error", error=str(e))
    hawk_client = None


def capture_exception(exception: Exception):
    """
    Отправляет исключение в Hawk для трекинга
    
    Args:
        exception: Исключение для отправки
    """
    if not hawk_client:
        return
    
    try:
        hawk_client.send(exception)
        logger.error("Error sent to Hawk", error=str(exception))
    except Exception as e:
        logger.error("hawk_send_error", error=str(e))

