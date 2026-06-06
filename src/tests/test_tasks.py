"""
Task tests — two levels:
  Route tests  : validate HTTP contract (status codes, JSON shape, auth guards)
  Service tests: validate business logic (filters, ownership, state transitions)
"""
import pytest
from datetime import datetime, timedelta


# =============================================================================
# ROUTE TESTS
# HTTP contract: status codes, response shape, auth redirection
# =============================================================================

class TestCreateTaskRoute:
    URL = "/tasks"

    def test_success_returns_201_with_task(self, auth_client):
        res = auth_client.post(self.URL, json={"title": "Buy milk"})
        assert res.status_code == 201
        data = res.get_json()["task"]
        assert data["title"] == "Buy milk"
        assert data["priority"] == "medium"
        assert data["status"] == "pending"
        assert data["is_done"] is False

    def test_with_all_optional_fields(self, auth_client):
        res = auth_client.post(self.URL, json={
            "title": "Study",
            "description": "Chapter 5",
            "deadline": "2026-12-31T23:59",
            "priority": "high",
            "reminder_minutes": 60,
        })
        assert res.status_code == 201
        data = res.get_json()["task"]
        assert data["priority"] == "high"
        assert data["reminder_minutes"] == 60
        assert "2026-12-31" in data["deadline"]

    def test_missing_title_returns_400(self, auth_client):
        assert auth_client.post(self.URL, json={"description": "No title"}).status_code == 400

    def test_invalid_priority_returns_400(self, auth_client):
        assert auth_client.post(self.URL, json={"title": "T", "priority": "urgent"}).status_code == 400

    def test_unauthenticated_redirects(self, client):
        assert client.post(self.URL, json={"title": "T"}).status_code == 302


class TestGetTasksRoute:
    URL = "/tasks"

    def test_returns_200(self, auth_client, task):
        assert auth_client.get(self.URL).status_code == 200

    def test_filter_completed(self, auth_client, db, user):
        from src.database.models import Task, Priority, TaskStatus
        db.session.add(Task(user_id=user.id, title="Done",
                            priority=Priority.low, status=TaskStatus.completed, is_done=True))
        db.session.commit()
        assert auth_client.get(f"{self.URL}?filter=completed").status_code == 200

    def test_filter_pending(self, auth_client, task):
        assert auth_client.get(f"{self.URL}?filter=pending").status_code == 200

    def test_filter_overdue(self, auth_client, overdue_task):
        assert auth_client.get(f"{self.URL}?filter=overdue").status_code == 200

    def test_unauthenticated_redirects(self, client):
        assert client.get(self.URL).status_code == 302


class TestEditTaskRoute:
    def test_success_returns_updated_task(self, auth_client, task):
        res = auth_client.put(f"/tasks/{task.id}/edit", json={"title": "Updated"})
        assert res.status_code == 200
        assert res.get_json()["task"]["title"] == "Updated"

    def test_partial_update_preserves_other_fields(self, auth_client, task):
        res = auth_client.put(f"/tasks/{task.id}/edit", json={"priority": "high"})
        assert res.status_code == 200
        assert res.get_json()["task"]["title"] == task.title

    def test_nonexistent_task_returns_404(self, auth_client):
        assert auth_client.put("/tasks/99999/edit", json={"title": "X"}).status_code == 404

    def test_other_users_task_returns_404(self, client, task, other_user):
        with client.session_transaction() as sess:
            sess["user_id"] = other_user.id
        assert client.put(f"/tasks/{task.id}/edit", json={"title": "Stolen"}).status_code == 404


class TestCompleteTaskRoute:
    def test_complete_returns_200_and_is_done_true(self, auth_client, task):
        res = auth_client.put(f"/tasks/{task.id}/complete")
        assert res.status_code == 200
        data = res.get_json()["task"]
        assert data["is_done"] is True
        assert data["status"] == "completed"

    def test_uncomplete_returns_200_and_is_done_false(self, auth_client, task, db):
        from src.database.models import TaskStatus
        task.is_done = True
        task.status = TaskStatus.completed
        db.session.commit()
        res = auth_client.put(f"/tasks/{task.id}/uncomplete")
        assert res.status_code == 200
        assert res.get_json()["task"]["is_done"] is False

    def test_complete_nonexistent_returns_404(self, auth_client):
        assert auth_client.put("/tasks/99999/complete").status_code == 404


class TestDeleteTaskRoute:
    def test_success_returns_200(self, auth_client, task):
        assert auth_client.delete(f"/tasks/{task.id}/delete").status_code == 200

    def test_nonexistent_returns_404(self, auth_client):
        assert auth_client.delete("/tasks/99999/delete").status_code == 404

    def test_record_removed_from_db(self, auth_client, task, db):
        from src.database.models import Task
        task_id = task.id
        auth_client.delete(f"/tasks/{task_id}/delete")
        assert db.session.get(Task, task_id) is None


# =============================================================================
# SERVICE TESTS
# Business logic: filters, ownership checks, state transitions, persistence
# =============================================================================

class TestTaskServiceCreate:
    def test_returns_task_with_correct_fields(self, db, user):
        from src.dto.task_dto import TaskCreateDTO
        from src.services.task_service import TaskService
        task = TaskService.create_task(user.id, TaskCreateDTO(title="Buy milk"))
        assert task.id is not None
        assert task.title == "Buy milk"
        assert task.user_id == user.id

    def test_default_status_is_pending(self, db, user):
        from src.database.models import TaskStatus
        from src.dto.task_dto import TaskCreateDTO
        from src.services.task_service import TaskService
        task = TaskService.create_task(user.id, TaskCreateDTO(title="T"))
        assert task.status == TaskStatus.pending
        assert task.is_done is False

    def test_default_priority_is_medium(self, db, user):
        from src.database.models import Priority
        from src.dto.task_dto import TaskCreateDTO
        from src.services.task_service import TaskService
        task = TaskService.create_task(user.id, TaskCreateDTO(title="T"))
        assert task.priority == Priority.medium

    def test_deadline_string_parsed_to_datetime(self, db, user):
        from src.dto.task_dto import TaskCreateDTO
        from src.services.task_service import TaskService
        task = TaskService.create_task(user.id, TaskCreateDTO(title="T", deadline="2026-12-31T10:00"))
        assert task.deadline == datetime(2026, 12, 31, 10, 0)


class TestTaskServiceGetTasks:
    def test_returns_all_tasks_for_user(self, db, user, task):
        from src.services.task_service import TaskService
        tasks = TaskService.get_tasks_for_user(user.id, "all")
        assert len(tasks) == 1 and tasks[0].id == task.id

    def test_filter_completed(self, db, user, task):
        from src.database.models import TaskStatus
        from src.services.task_service import TaskService
        task.is_done = True
        task.status = TaskStatus.completed
        db.session.commit()
        assert len(TaskService.get_tasks_for_user(user.id, "completed")) == 1
        assert len(TaskService.get_tasks_for_user(user.id, "pending")) == 0

    def test_filter_pending(self, db, user, task):
        from src.services.task_service import TaskService
        assert len(TaskService.get_tasks_for_user(user.id, "pending")) == 1

    def test_filter_overdue(self, db, user, overdue_task):
        from src.services.task_service import TaskService
        tasks = TaskService.get_tasks_for_user(user.id, "overdue")
        assert any(t.id == overdue_task.id for t in tasks)

    def test_isolates_by_user(self, db, user, other_user, task):
        from src.services.task_service import TaskService
        assert TaskService.get_tasks_for_user(other_user.id, "all") == []


class TestTaskServiceEdit:
    def test_updates_title(self, db, user, task):
        from src.dto.task_dto import TaskUpdateDTO
        from src.services.task_service import TaskService
        updated = TaskService.edit_task(user.id, task.id, TaskUpdateDTO(title="New Title"))
        assert updated.title == "New Title"

    def test_partial_update_leaves_other_fields_unchanged(self, db, user, task):
        from src.dto.task_dto import TaskUpdateDTO
        from src.services.task_service import TaskService
        original_title = task.title
        TaskService.edit_task(user.id, task.id, TaskUpdateDTO(reminder_minutes=60))
        db.session.refresh(task)
        assert task.title == original_title
        assert task.reminder_minutes == 60

    def test_nonexistent_task_returns_none(self, db, user):
        from src.dto.task_dto import TaskUpdateDTO
        from src.services.task_service import TaskService
        assert TaskService.edit_task(user.id, 99999, TaskUpdateDTO(title="X")) is None

    def test_other_users_task_returns_none(self, db, user, other_user, task):
        from src.dto.task_dto import TaskUpdateDTO
        from src.services.task_service import TaskService
        assert TaskService.edit_task(other_user.id, task.id, TaskUpdateDTO(title="Stolen")) is None


class TestTaskServiceComplete:
    def test_complete_sets_is_done_and_status(self, db, user, task):
        from src.database.models import TaskStatus
        from src.services.task_service import TaskService
        result = TaskService.complete_task(user.id, task.id)
        assert result.is_done is True
        assert result.status == TaskStatus.completed

    def test_uncomplete_clears_is_done(self, db, user, task):
        from src.database.models import TaskStatus
        from src.services.task_service import TaskService
        task.is_done = True
        db.session.commit()
        result = TaskService.uncomplete_task(user.id, task.id)
        assert result.is_done is False
        assert result.status == TaskStatus.pending

    def test_nonexistent_task_returns_none(self, db, user):
        from src.services.task_service import TaskService
        assert TaskService.complete_task(user.id, 99999) is None


class TestTaskServiceDelete:
    def test_success_returns_true(self, db, user, task):
        from src.services.task_service import TaskService
        assert TaskService.delete_task(user.id, task.id) is True

    def test_record_removed_from_db(self, db, user, task):
        from src.database.models import Task
        from src.services.task_service import TaskService
        task_id = task.id
        TaskService.delete_task(user.id, task_id)
        assert db.session.get(Task, task_id) is None

    def test_nonexistent_returns_false(self, db, user):
        from src.services.task_service import TaskService
        assert TaskService.delete_task(user.id, 99999) is False

    def test_other_users_task_returns_false(self, db, user, other_user, task):
        from src.services.task_service import TaskService
        assert TaskService.delete_task(other_user.id, task.id) is False
