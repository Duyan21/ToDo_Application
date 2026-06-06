import logging
import os
from datetime import datetime
from typing import Optional, Tuple
from src.dto.task_dto import TaskCreateDTO, TaskUpdateDTO
from src.repositories import (
    get_task_repository,
    get_file_repository,
)
from src.database.models import (
    Task,
    TaskStatus,
    Priority,
)
from src.utils.generators.read_csv import read_tasks_from_csv

logger = logging.getLogger(__name__)


class TaskService:

    @staticmethod
    def get_tasks_for_user(user_id, filter_type="all"):
        task_repository = get_task_repository()
        return task_repository.get_tasks_for_user(user_id, filter_type)

    @staticmethod
    def create_task(user_id: int, task_create_dto: TaskCreateDTO):
        new_task = get_task_repository().create(
            user_id=user_id,
            title=task_create_dto.title,
            description=task_create_dto.description,
            deadline=task_create_dto.deadline,
            priority=task_create_dto.priority,
            status=TaskStatus.pending,
            reminder_minutes=task_create_dto.reminder_minutes,
        )
        return new_task

    @staticmethod
    def get_task_by_id_for_user(task_id: int, user_id: int) -> Optional[Task]:
        task_repository = get_task_repository()
        return task_repository.get_by_id_for_user(task_id, user_id)

    @staticmethod
    def edit_task(
        user_id: int, task_id: int, task_update_dto: TaskUpdateDTO
    ) -> Optional[Task]:
        """Edit a task with the provided data."""
        task_repository = get_task_repository()

        # Prepare update data
        update_data = {}
        if task_update_dto.title:
            update_data["title"] = task_update_dto.title
        if task_update_dto.description is not None:
            update_data["description"] = task_update_dto.description
        if task_update_dto.priority:
            update_data["priority"] = task_update_dto.priority
        if task_update_dto.reminder_minutes is not None:
            update_data["reminder_minutes"] = task_update_dto.reminder_minutes
        if task_update_dto.deadline:
            update_data["deadline"] = datetime.strptime(
                task_update_dto.deadline, "%Y-%m-%dT%H:%M"
            )

        task = task_repository.update_task_for_user(task_id, user_id, **update_data)
        if task:
            logger.info("Task %s updated.", task_id)
        return task

    @staticmethod
    def complete_task(user_id: int, task_id: int) -> Optional[Task]:
        """Mark a task as completed."""
        task_repository = get_task_repository()
        task = task_repository.complete_task(task_id, user_id)
        if task:
            logger.info("Task %s completed.", task_id)
        return task

    @staticmethod
    def uncomplete_task(user_id: int, task_id: int) -> Optional[Task]:
        """Mark a task as uncompleted."""
        task_repository = get_task_repository()
        task = task_repository.uncomplete_task(task_id, user_id)
        if task:
            logger.info("Task %s uncompleted.", task_id)
        return task

    @staticmethod
    def delete_task(user_id: int, task_id: int) -> bool:
        """Delete a task."""
        task_repository = get_task_repository()
        deleted = task_repository.delete_task_for_user(task_id, user_id)
        if deleted:
            logger.info("Task %s deleted.", task_id)
        return deleted

    @staticmethod
    def import_tasks_from_csv(
        user_id: int, file_path: str, file_id: int
    ) -> Tuple[bool, str]:
        """Import tasks from CSV file. Returns (success, message)."""
        task_repository = get_task_repository()
        file_repository = get_file_repository()

        try:
            # Verify file exists for the user
            file_record = file_repository.get_file_for_user(file_id, user_id)
            if not file_record:
                return False, "Không tìm thấy file."

            if file_record.is_imported:
                return False, "File đã được nhập trước đó."

            if not file_path or not os.path.exists(file_path):
                return False, "File không tồn tại trên server."

            # Read and import tasks
            for parts in read_tasks_from_csv(file_path):
                if len(parts) < 1:
                    continue

                title = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ""
                deadline_str = parts[2].strip() if len(parts) > 2 else ""
                deadline = (
                    datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
                    if deadline_str
                    else None
                )
                priority_str = parts[3].strip() if len(parts) > 3 else "medium"
                try:
                    priority_str = Priority(priority_str).value
                except ValueError:
                    priority_str = Priority.medium.value
                reminder_minutes = (
                    int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0
                )

                task_create_dto = TaskCreateDTO(
                    title=title,
                    description=description,
                    deadline=deadline,
                    priority=priority_str,
                    reminder_minutes=reminder_minutes,
                )
                task_repository.create(
                    user_id=user_id,
                    title=task_create_dto.title,
                    description=task_create_dto.description,
                    deadline=task_create_dto.deadline,
                    priority=task_create_dto.priority,
                    status=TaskStatus.pending,
                    reminder_minutes=task_create_dto.reminder_minutes,
                )

            # Update file import status
            file_repository.update_file_import_status(file_id, user_id, True)
            logger.info("Tasks imported from file %s for user %s.", file_id, user_id)
            return True, "Nhập tasks thành công!"

        except Exception as e:
            logger.error("Error importing tasks: %s", str(e))
            return False, f"Lỗi khi nhập tasks: {str(e)}"
