from typing import Any, List, Optional

from flask_sqlalchemy import SQLAlchemy

from src.database.models import User
from src.repositories.base_repository import AbstractRepository


class UserRepository(AbstractRepository):
    def __init__(self, db: SQLAlchemy):
        self._db = db
        self.model = User

    def create(self, **kwargs: Any) -> User:
        try:
            entity = self.model(**kwargs)
            self._db.session.add(entity)
            self._db.session.commit()
            return entity
        except Exception as e:
            self._db.session.rollback()
            raise e

    def get_by_id(self, entity_id: int) -> Optional[User]:
        return self.model.query.get(entity_id)

    def get_all(self) -> List[User]:
        return self.model.query.all()

    def find(self, **filters: Any) -> List[User]:
        return self.model.query.filter_by(**filters).all()

    def first(self, **filters: Any) -> Optional[User]:
        return self.model.query.filter_by(**filters).first()

    def update(self, entity_id: int, **kwargs: Any) -> Optional[User]:
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

    def custom_query(self, **kwargs) -> List[User]:
        return self.find(**kwargs)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.first(email=email)

    def get_by_name(self, name: str) -> Optional[User]:
        return self.first(name=name)
