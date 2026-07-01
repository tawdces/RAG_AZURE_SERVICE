import logging
from azure.monitor.opentelemetry import configure_azure_monitor
from src.config import APPLICATIONINSIGHTS_CONNECTION_STRING

_configured = False


def setup_logging() -> logging.Logger:
    """ตั้งค่า Azure Application Insights (logging + tracing + metrics)"""
    global _configured

    logger = logging.getLogger("app")

    if _configured:
        return logger

    if not APPLICATIONINSIGHTS_CONNECTION_STRING:
        logging.basicConfig(level=logging.INFO)
        logger.warning(
            "APPLICATIONINSIGHTS_CONNECTION_STRING not set, "
            "using local logging only (no data sent to Azure)"
        )
        _configured = True
        return logger

    configure_azure_monitor(
        connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING,
        logger_name="app",
    )
    logger.setLevel(logging.INFO)

    _configured = True
    return logger


logger = setup_logging()