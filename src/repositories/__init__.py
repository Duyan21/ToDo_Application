from src.database import get_db
from src.repositories.file_repository import FileRepository
from src.repositories.notification_repository import NotificationRepository
from src.repositories.task_repository import TaskRepository
from src.repositories.user_repository import UserRepository

__file_repository = None
__notification_repository = None
__task_repository = None
__user_repository = None


def get_file_repository() -> FileRepository:
    global __file_repository
    if __file_repository is None:
        __file_repository = FileRepository(get_db())
    return __file_repository


def get_notification_repository() -> NotificationRepository:
    global __notification_repository
    if __notification_repository is None:
        __notification_repository = NotificationRepository(get_db())
    return __notification_repository


def get_task_repository() -> TaskRepository:
    global __task_repository
    if __task_repository is None:
        __task_repository = TaskRepository(get_db())
    return __task_repository


def get_user_repository() -> UserRepository:
    global __user_repository
    if __user_repository is None:
        __user_repository = UserRepository(get_db())
    return __user_repository


__all__ = [
    "get_file_repository",
    "get_notification_repository",
    "get_task_repository",
    "get_user_repository",
]
