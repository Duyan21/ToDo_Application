from typing import Any, List, Optional
from flask_sqlalchemy import SQLAlchemy
from src.database.models import Task
from src.repositories.base_repository import AbstractRepository
from datetime import datetime, timedelta


class TaskRepository(AbstractRepository):
    def __init__(self, db: SQLAlchemy):
        self._db = db
        self.model = Task

    def create(self, **kwargs: Any) -> Task:
        entity = self.model(**kwargs)
        self._db.session.add(entity)
        self._db.session.commit()
        return entity

    def get_by_id(self, entity_id: int) -> Optional[Task]:
        return self.model.query.get(entity_id)

    def get_all(self) -> List[Task]:
        return self.model.query.all()

    def find(self, **filters: Any) -> List[Task]:
        return self.model.query.filter_by(**filters).all()

    def first(self, **filters: Any) -> Optional[Task]:
        return self.model.query.filter_by(**filters).first()

    def update(self, entity_id: int, **kwargs: Any) -> Optional[Task]:
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

    def custom_query(self, **kwargs) -> List[Task]:
        return self.find(**kwargs)

    def get_by_user(self, user_id: int) -> List[Task]:
        return self.find(user_id=user_id)

    def get_pending(self, user_id: int) -> List[Task]:
        return self.find(user_id=user_id, status="pending")

    def get_completed(self, user_id: int) -> List[Task]:
        return self.find(user_id=user_id, status="completed")

    def get_users_with_tasks(self) -> List[int]:
        return [
            user_id
            for (user_id,) in self._db.session.query(Task.user_id).distinct().all()
        ]

    def get_tasks_for_user(self, user_id: int, filter_type: str = "all") -> List[Task]:
        query = self.model.query.filter_by(user_id=user_id)

        if filter_type == "completed":
            query = query.filter_by(is_done=True)
        elif filter_type == "pending":
            query = query.filter_by(is_done=False, status="pending")
        elif filter_type == "overdue":
            query = query.filter(
                self.model.is_done == False, self.model.deadline < datetime.now()
            )

        return query.all()

    def get_by_id_for_user(self, task_id: int, user_id: int) -> Optional[Task]:
        return self.model.query.filter_by(id=task_id, user_id=user_id).first()

    def update_task_for_user(
        self, task_id: int, user_id: int, **kwargs: Any
    ) -> Optional[Task]:
        """Update task for a specific user."""
        task = self.get_by_id_for_user(task_id, user_id)
        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        self._db.session.commit()
        return task

    def complete_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Mark a task as completed for a specific user."""
        from src.database.models import TaskStatus

        return self.update_task_for_user(
            task_id, user_id, is_done=True, status=TaskStatus.completed
        )

    def uncomplete_task(self, task_id: int, user_id: int) -> Optional[Task]:
        """Mark a task as uncompleted for a specific user."""
        from src.database.models import TaskStatus

        return self.update_task_for_user(
            task_id, user_id, is_done=False, status=TaskStatus.pending
        )

    def delete_task_for_user(self, task_id: int, user_id: int) -> bool:
        """Delete a task for a specific user."""
        task = self.get_by_id_for_user(task_id, user_id)
        if not task:
            return False

        self._db.session.delete(task)
        self._db.session.commit()
        return True
