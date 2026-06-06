"""Unit tests for all DTOs — pure Python, no DB or Flask needed."""
import json
from datetime import datetime
from types import SimpleNamespace

import pytest


def make_file(**kwargs):
    defaults = dict(
        id=1, user_id=1,
        filename="tasks.csv",
        file_path="upload/tasks.csv",
        is_imported=False,
        uploaded_at=datetime(2026, 1, 1, 10, 0),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── helpers ───────────────────────────────────────────────────────────────────

def make_task(**kwargs):
    from src.database.models import Priority, TaskStatus
    defaults = dict(
        id=1, title="Task", description=None, deadline=None,
        priority=Priority.medium, status=TaskStatus.pending,
        reminder_minutes=0, is_done=False, user_id=1,
        created_at=datetime(2026, 1, 1),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_notification(**kwargs):
    from src.database.models import NotificationType
    defaults = dict(
        id=1, task_id=1, user_id=1,
        type=NotificationType.OVERDUE, message="msg",
        notify_time=datetime(2026, 1, 1), sent=False,
        is_read=False, created_at=datetime(2026, 1, 1),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── UserRegisterDTO ───────────────────────────────────────────────────────────

class TestUserRegisterDTO:
    def test_name_is_stripped(self):
        from src.dto.user_dto import UserRegisterDTO
        dto = UserRegisterDTO(name="  Alice  ", email="a@b.com", password="pass")
        assert dto.name == "Alice"

    def test_email_is_lowercased(self):
        from src.dto.user_dto import UserRegisterDTO
        dto = UserRegisterDTO(name="A", email="TEST@EXAMPLE.COM", password="pass")
        assert dto.email == "test@example.com"

    def test_whitespace_name_stripped_to_empty(self):
        from src.dto.user_dto import UserRegisterDTO
        dto = UserRegisterDTO(name="   ", email="a@b.com", password="pass")
        assert dto.name == ""

    def test_email_whitespace_stripped(self):
        from src.dto.user_dto import UserRegisterDTO
        dto = UserRegisterDTO(name="A", email="  user@test.com  ", password="pass")
        assert dto.email == "user@test.com"


# ── UserLoginDTO ──────────────────────────────────────────────────────────────

class TestUserLoginDTO:
    def test_email_lowercased(self):
        from src.dto.user_dto import UserLoginDTO
        dto = UserLoginDTO(email="USER@DOMAIN.COM", password="pass")
        assert dto.email == "user@domain.com"

    def test_email_whitespace_stripped(self):
        from src.dto.user_dto import UserLoginDTO
        dto = UserLoginDTO(email="  user@domain.com  ", password="pass")
        assert dto.email == "user@domain.com"


# ── TaskDTO ───────────────────────────────────────────────────────────────────

class TestTaskDTO:
    def test_from_model_extracts_priority_as_string(self):
        from src.database.models import Priority
        from src.dto.task_dto import TaskDTO
        dto = TaskDTO.from_model(make_task(priority=Priority.high))
        assert dto.priority == "high"

    def test_from_model_extracts_status_as_string(self):
        from src.database.models import TaskStatus
        from src.dto.task_dto import TaskDTO
        dto = TaskDTO.from_model(make_task(status=TaskStatus.completed))
        assert dto.status == "completed"

    def test_to_dict_priority_is_string(self):
        from src.database.models import Priority
        from src.dto.task_dto import TaskDTO
        result = TaskDTO.from_model(make_task(priority=Priority.low)).to_dict()
        assert result["priority"] == "low"
        assert isinstance(result["priority"], str)

    def test_to_dict_deadline_isoformat(self):
        from src.dto.task_dto import TaskDTO
        dl = datetime(2026, 6, 15, 10, 30)
        result = TaskDTO.from_model(make_task(deadline=dl)).to_dict()
        assert result["deadline"] == dl.isoformat()

    def test_to_dict_none_deadline(self):
        from src.dto.task_dto import TaskDTO
        assert TaskDTO.from_model(make_task(deadline=None)).to_dict()["deadline"] is None

    def test_to_dict_is_json_serializable(self):
        from src.dto.task_dto import TaskDTO
        json.dumps(TaskDTO.from_model(make_task()).to_dict())


# ── TaskCreateDTO ─────────────────────────────────────────────────────────────

class TestTaskCreateDTO:
    def test_parses_deadline_string(self):
        from src.dto.task_dto import TaskCreateDTO
        dto = TaskCreateDTO(title="T", deadline="2026-12-31T09:00")
        assert isinstance(dto.deadline, datetime)
        assert dto.deadline == datetime(2026, 12, 31, 9, 0)

    def test_none_deadline_stays_none(self):
        from src.dto.task_dto import TaskCreateDTO
        assert TaskCreateDTO(title="T", deadline=None).deadline is None

    def test_invalid_deadline_raises(self):
        from src.dto.task_dto import TaskCreateDTO
        with pytest.raises(ValueError):
            TaskCreateDTO(title="T", deadline="not-a-date")

    def test_default_priority_is_medium(self):
        from src.dto.task_dto import TaskCreateDTO
        assert TaskCreateDTO(title="T").priority == "medium"

    def test_default_reminder_is_zero(self):
        from src.dto.task_dto import TaskCreateDTO
        assert TaskCreateDTO(title="T").reminder_minutes == 0


# ── NotificationDTO ───────────────────────────────────────────────────────────

class TestNotificationDTO:
    def test_from_model_extracts_type_as_string(self):
        from src.database.models import NotificationType
        from src.dto.notification_dto import NotificationDTO
        dto = NotificationDTO.from_model(make_notification(type=NotificationType.REMINDER))
        assert dto.type == "REMINDER"
        assert isinstance(dto.type, str)

    def test_to_dict_notify_time_isoformat(self):
        from src.dto.notification_dto import NotificationDTO
        t = datetime(2026, 6, 1, 8, 0)
        result = NotificationDTO.from_model(make_notification(notify_time=t)).to_dict()
        assert result["notify_time"] == t.isoformat()

    def test_to_dict_none_notify_time(self):
        from src.dto.notification_dto import NotificationDTO
        result = NotificationDTO.from_model(make_notification(notify_time=None)).to_dict()
        assert result["notify_time"] is None

    def test_to_dict_is_json_serializable(self):
        from src.dto.notification_dto import NotificationDTO
        json.dumps(NotificationDTO.from_model(make_notification()).to_dict())


# ── FileDTO ───────────────────────────────────────────────────────────────────

class TestFileDTO:
    def test_from_model_maps_filename(self):
        from src.dto.file_dto import FileDTO
        dto = FileDTO.from_model(make_file(filename="import.csv"))
        assert dto.filename == "import.csv"

    def test_from_model_maps_file_path(self):
        from src.dto.file_dto import FileDTO
        dto = FileDTO.from_model(make_file(file_path="upload/import.csv"))
        assert dto.file_path == "upload/import.csv"

    def test_from_model_maps_is_imported(self):
        from src.dto.file_dto import FileDTO
        dto = FileDTO.from_model(make_file(is_imported=True))
        assert dto.is_imported is True

    def test_to_dict_uploaded_at_isoformat(self):
        from src.dto.file_dto import FileDTO
        t = datetime(2026, 6, 1, 12, 0)
        result = FileDTO.from_model(make_file(uploaded_at=t)).to_dict()
        assert result["uploaded_at"] == t.isoformat()

    def test_to_dict_none_uploaded_at(self):
        from src.dto.file_dto import FileDTO
        result = FileDTO.from_model(make_file(uploaded_at=None)).to_dict()
        assert result["uploaded_at"] is None

    def test_to_dict_is_json_serializable(self):
        from src.dto.file_dto import FileDTO
        json.dumps(FileDTO.from_model(make_file()).to_dict())

    def test_to_dict_has_correct_keys(self):
        from src.dto.file_dto import FileDTO
        result = FileDTO.from_model(make_file()).to_dict()
        assert set(result.keys()) == {"id", "user_id", "filename", "file_path", "is_imported", "uploaded_at"}


# ── TaskCreateDTO — datetime passthrough (CSV import path) ────────────────────

class TestTaskCreateDTODatetimePassthrough:
    def test_datetime_object_not_reparsed(self):
        """CSV import passes deadline as datetime; __post_init__ must not crash."""
        from src.dto.task_dto import TaskCreateDTO
        dl = datetime(2026, 12, 31, 9, 0)
        dto = TaskCreateDTO(title="T", deadline=dl)
        assert dto.deadline == dl

    def test_string_still_parsed(self):
        from src.dto.task_dto import TaskCreateDTO
        dto = TaskCreateDTO(title="T", deadline="2026-12-31T09:00")
        assert dto.deadline == datetime(2026, 12, 31, 9, 0)
