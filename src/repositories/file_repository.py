from typing import Any, List, Optional
from flask_sqlalchemy import SQLAlchemy
from src.database.models import File
from src.repositories.base_repository import AbstractRepository


class FileRepository(AbstractRepository):
    def __init__(self, db: SQLAlchemy):
        self._db = db
        self.model = File

    def create(self, **kwargs: Any) -> File:
        entity = self.model(**kwargs)
        self._db.session.add(entity)
        self._db.session.commit()
        return entity

    def get_by_id(self, entity_id: int) -> Optional[File]:
        return self._db.session.get(self.model, entity_id)

    def get_all(self) -> List[File]:
        return self.model.query.all()

    def find(self, **filters: Any) -> List[File]:
        return self.model.query.filter_by(**filters).all()

    def first(self, **filters: Any) -> Optional[File]:
        return self.model.query.filter_by(**filters).first()

    def update(self, entity_id: int, **kwargs: Any) -> Optional[File]:
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

    def custom_query(self, **kwargs) -> List[File]:
        return self.find(**kwargs)

    def get_by_user(self, user_id: int) -> List[File]:
        return self.find(user_id=user_id)

    def get_by_filename(self, filename: str) -> Optional[File]:
        return self.first(filename=filename)

    def get_files_for_user_with_filter(
        self, user_id: int, filter_type: str = "all"
    ) -> List[File]:
        """Get files for a specific user with optional filter."""
        query = self.model.query.filter_by(user_id=user_id)

        if filter_type == "pending":
            query = query.filter(self.model.is_imported == False)
        elif filter_type == "imported":
            query = query.filter(self.model.is_imported == True)

        return query.all()

    def update_file_import_status(
        self, file_id: int, user_id: int, is_imported: bool
    ) -> Optional[File]:
        """Update import status for a specific file."""
        file_record = self.model.query.filter_by(id=file_id, user_id=user_id).first()
        if not file_record:
            return None

        file_record.is_imported = is_imported
        self._db.session.commit()
        return file_record

    def get_file_for_user(self, file_id: int, user_id: int) -> Optional[File]:
        """Get a specific file for a user."""
        return self.model.query.filter_by(id=file_id, user_id=user_id).first()
