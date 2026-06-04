from src.database.models import db

__db__ = None
def get_db():
    global __db__
    if __db__ is None:
        __db__ = db
    return __db__