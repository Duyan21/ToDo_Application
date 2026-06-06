from typing import Any, List, Optional
from flask_sqlalchemy import SQLAlchemy
from src.database.models import Notification
from src.repositories.base_repository import AbstractRepository


class NotificationRepository(AbstractRepository):
    def __init__(self, db: SQLAlchemy):
        self._db = db
        self.model = Notification

    def create(self, **kwargs: Any) -> Notification:
        entity = self.model(**kwargs)
        self._db.session.add(entity)
        self._db.session.commit()
        return entity

    def get_by_id(self, entity_id: int) -> Optional[Notification]:
        return self._db.session.get(self.model, entity_id)

    def get_all(self) -> List[Notification]:
        return self.model.query.all()

    def find(self, order_by=None, **filters: Any) -> List[Notification]:
        query = self.model.query

        for key, value in filters.items():
            if isinstance(value, (list, tuple, set)):
                query = query.filter(getattr(self.model, key).in_(value))
            else:
                query = query.filter_by(**{key: value})

        if order_by:
            for order in order_by:
                if isinstance(order, tuple) and len(order) == 2:
                    field, direction = order
                    col = field if hasattr(field, "asc") else getattr(self.model, field)
                    query = query.order_by(col.asc() if str(direction).lower() == "asc" else col.desc())
                else:
                    query = query.order_by(order)

        return query.all()

    def first(self, **filters: Any) -> Optional[Notification]:
        return self.model.query.filter_by(**filters).first()

    def update(self, entity_id: int, **kwargs: Any) -> Optional[Notification]:
        entity = self.get_by_id(entity_id)
        if not entity:
            return None

        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

        self._db.session.commit()
        return entity

    def delete(self, entity_id: int) -> bool:
        entity = self.get_by_id(entity_id)
        if not entity:
            return False

        self._db.session.delete(entity)
        self._db.session.commit()
        return True

    def delete_all(self) -> int:
        deleted = self.model.query.delete()
        self._db.session.commit()
        return deleted

    def custom_query(self, **kwargs) -> List[Notification]:
        return self.find(**kwargs)

    def get_by_user(self, user_id: int) -> List[Notification]:
        return self.find(user_id=user_id)

    def get_by_task(self, task_id: int) -> List[Notification]:
        return self.find(task_id=task_id)

    def get_unread(self, user_id: int) -> List[Notification]:
        return self.find(user_id=user_id, is_read=False)

    def delete_by_user_id(self, user_id: int) -> int:
        counted = self.model.query.filter_by(user_id=user_id).count()
        self.model.query.filter_by(user_id=user_id).delete()
        self._db.session.commit()
        return counted
