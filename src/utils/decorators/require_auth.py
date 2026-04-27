from flask import session, jsonify
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            logger.warning("Unauthorized access attempt for %s", func.__name__)
            return jsonify({"error": "You must be logged in to access this resource"}), 401
        return func(*args, **kwargs)
    return wrapper