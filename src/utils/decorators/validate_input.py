from functools import wraps
import logging
from flask import jsonify, request

logger = logging.getLogger(__name__)

def validate_input(**rules):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json() or {}

            required_rules = rules.get('required_fields', [])
            field_types = rules.get('field_types', {})
            enum_fields = rules.get('enum_fields', {})

            missing = [f for f in required_rules 
                      if f not in data or data.get(f) is None]

            missing = list(filter(lambda f: f not in data or data.get(f) is None, required_rules))
            
            if missing:
                msg = f"Thiếu: {', '.join(missing)}"
                logger.warning("Validation failed for %s: %s", func.__name__, msg)
                return jsonify({"error": msg}), 400

            for field, ftype in field_types.items():
                if field in data and data[field] is not None:
                    if not isinstance(data[field], ftype):
                        msg = f"'{field}' phải là {ftype.__name__}, nhận {type(data[field]).__name__}"
                        logger.warning("Validation failed for %s: %s", func.__name__, msg)
                        return jsonify({"error": msg}), 400

            for field, values in enum_fields.items():
                if field in data and data[field] not in values:
                    msg = f"'{field}' phải là: {', '.join(map(str, values))}"
                    logger.warning("Validation failed for %s: %s", func.__name__, msg)
                    return jsonify({"error": msg}), 400

            logger.info("Validation passed for %s", func.__name__)
            return func(*args, **kwargs)
        return wrapper
    return decorator