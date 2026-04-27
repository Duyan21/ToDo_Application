import logging
from functools import wraps

logger = logging.getLogger(__name__)


def log_api_decorator(func):
    @wraps(func)
    def wrapper_function(*args, **kwargs):
        logger.info(
            "Begin %s: module=%s args=%s kwargs=%s",
            func.__name__, func.__module__, args, kwargs
        )
        try:
            response = func(*args, **kwargs)
            status = getattr(response, 'status_code', None)
            logger.info(
                "End %s: status=%s response_type=%s",
                func.__name__, status, type(response).__name__
            )
            return response
        except Exception:
            logger.exception("Error in %s", func.__name__)
            raise
    return wrapper_function
