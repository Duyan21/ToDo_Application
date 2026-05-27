import logging
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import jsonify, redirect, request, session, url_for

logger = logging.getLogger(__name__)


def require_auth(func: Callable[..., Any] | None = None, *, api: bool | None = None) -> Any:
    """Auth guard decorator.

    Usage:
        @require_auth              — infers response type from URL prefix
        @require_auth(api=True)    — always return JSON 401
        @require_auth(api=False)   — always redirect to sign-in
    """
    def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not session.get('user_id'):
                logger.warning("Unauthorized access attempt for %s", f.__name__)
                use_api = api if api is not None else request.path.startswith('/api/')
                if use_api:
                    return jsonify({"error": "Bạn cần đăng nhập để truy cập tài nguyên này"}), 401
                return redirect(url_for('auth.signin_page'))
            return f(*args, **kwargs)
        return wrapper

    if func is not None:
        # Used as @require_auth (no call) — decorate immediately
        return decorator(func)
    # Used as @require_auth(...) — return the decorator
    return decorator
