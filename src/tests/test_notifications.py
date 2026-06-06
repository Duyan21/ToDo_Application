"""
Notification tests — two levels:
  Route tests  : validate HTTP contract (status codes, JSON shape, auth guards)
  Service tests: validate sync logic, read/unread state, ownership isolation
"""
import pytest
from datetime import datetime, timedelta


# ── Shared helpers ────────────────────────────────────────────────────────────

def _add_notification(db, user, task, ntype, is_read=False):
    from src.database.models import Notification, NotificationType
    n = Notification(
        task_id=task.id, user_id=user.id,
        type=NotificationType[ntype],
        message=f"Test {ntype}",
        notify_time=datetime.now(),
        is_read=is_read,
    )
    db.session.add(n)
    db.session.commit()
    db.session.refresh(n)
    return n


def _add_task(db, user, deadline, reminder_minutes=0, is_done=False):
    from src.database.models import Task, Priority, TaskStatus
    t = Task(
        user_id=user.id, title="Task",
        priority=Priority.medium,
        status=TaskStatus.completed if is_done else TaskStatus.pending,
        deadline=deadline,
        reminder_minutes=reminder_minutes,
        is_done=is_done,
    )
    db.session.add(t)
    db.session.commit()
    db.session.refresh(t)
    return t


# =============================================================================
# ROUTE TESTS
# HTTP contract: status codes, JSON shape, unread count, auth redirection
# =============================================================================

class TestGetNotificationsRoute:
    URL = "/notifications"

    def test_empty_list_returns_200_with_zero_unread(self, auth_client):
        res = auth_client.get(self.URL)
        assert res.status_code == 200
        data = res.get_json()
        assert data["notifications"] == []
        assert data["unread_count"] == 0

    def test_returns_notifications_and_correct_unread_count(self, auth_client, db, user, task):
        _add_notification(db, user, task, "OVERDUE")
        res = auth_client.get(self.URL)
        data = res.get_json()
        assert len(data["notifications"]) == 1
        assert data["unread_count"] == 1

    def test_read_notification_not_counted_as_unread(self, auth_client, db, user, task):
        _add_notification(db, user, task, "OVERDUE", is_read=True)
        assert auth_client.get(self.URL).get_json()["unread_count"] == 0

    def test_overdue_sorted_before_reminder(self, auth_client, db, user, task, overdue_task):
        _add_notification(db, user, task, "REMINDER")
        _add_notification(db, user, overdue_task, "OVERDUE")
        types = [n["type"] for n in auth_client.get(self.URL).get_json()["notifications"]]
        assert types[0] == "OVERDUE"

    def test_unauthenticated_redirects(self, client):
        assert client.get(self.URL).status_code == 302


class TestMarkNotificationReadRoute:
    def test_success_returns_200(self, auth_client, db, user, task):
        n = _add_notification(db, user, task, "OVERDUE")
        assert auth_client.post(f"/notifications/{n.id}/read").status_code == 200

    def test_notification_is_read_in_db(self, auth_client, db, user, task):
        from src.database.models import Notification
        n = _add_notification(db, user, task, "OVERDUE")
        auth_client.post(f"/notifications/{n.id}/read")
        assert db.session.get(Notification, n.id).is_read is True

    def test_nonexistent_returns_404(self, auth_client):
        assert auth_client.post("/notifications/99999/read").status_code == 404

    def test_other_users_notification_returns_404(self, client, db, user, task, other_user):
        n = _add_notification(db, user, task, "REMINDER")
        with client.session_transaction() as sess:
            sess["user_id"] = other_user.id
        assert client.post(f"/notifications/{n.id}/read").status_code == 404


class TestMarkAllReadRoute:
    URL = "/notifications/read-all"

    def test_success_returns_200(self, auth_client, db, user, task):
        _add_notification(db, user, task, "OVERDUE")
        assert auth_client.post(self.URL).status_code == 200

    def test_all_notifications_marked_read(self, auth_client, db, user, task):
        from src.database.models import Notification
        _add_notification(db, user, task, "OVERDUE")
        _add_notification(db, user, task, "REMINDER")
        auth_client.post(self.URL)
        assert Notification.query.filter_by(user_id=user.id, is_read=False).count() == 0

    def test_unauthenticated_redirects(self, client):
        assert client.post(self.URL).status_code == 302


class TestClearNotificationsRoute:
    URL = "/notifications/clear"

    def test_success_returns_200(self, auth_client, db, user, task):
        _add_notification(db, user, task, "OVERDUE")
        assert auth_client.post(self.URL).status_code == 200

    def test_response_message_includes_count(self, auth_client, db, user, task):
        _add_notification(db, user, task, "OVERDUE")
        assert "1" in auth_client.post(self.URL).get_json()["message"]

    def test_all_notifications_removed_from_db(self, auth_client, db, user, task):
        from src.database.models import Notification
        _add_notification(db, user, task, "OVERDUE")
        _add_notification(db, user, task, "REMINDER")
        auth_client.post(self.URL)
        assert Notification.query.filter_by(user_id=user.id).count() == 0

    def test_unauthenticated_redirects(self, client):
        assert client.post(self.URL).status_code == 302


# =============================================================================
# SERVICE TESTS
# Sync logic, time-based triggering, state transitions, ownership isolation
# =============================================================================

class TestNotificationSync:
    """_sync_notifications_for_user(user_id, now) — `now` is injected so tests
    are deterministic without patching datetime."""

    def _sync(self, db, user_id, now=None):
        from src.services.notification_service import NotificationService
        NotificationService._sync_notifications_for_user(user_id, now or datetime.now())

    def _count(self, db, user):
        from src.database.models import Notification
        return Notification.query.filter_by(user_id=user.id).count()

    def test_overdue_task_creates_overdue_notification(self, db, user):
        from src.database.models import Notification, NotificationType
        now = datetime.now()
        _add_task(db, user, deadline=now - timedelta(hours=2))
        self._sync(db, user.id, now)
        assert Notification.query.filter_by(user_id=user.id, type=NotificationType.OVERDUE).count() == 1

    def test_task_in_reminder_window_creates_reminder(self, db, user):
        from src.database.models import Notification, NotificationType
        now = datetime.now()
        # deadline 30 min away, reminder 60 min → reminder_time already passed
        _add_task(db, user, deadline=now + timedelta(minutes=30), reminder_minutes=60)
        self._sync(db, user.id, now)
        assert Notification.query.filter_by(user_id=user.id, type=NotificationType.REMINDER).count() == 1

    def test_future_task_outside_reminder_window_no_notification(self, db, user):
        now = datetime.now()
        _add_task(db, user, deadline=now + timedelta(hours=3), reminder_minutes=30)
        self._sync(db, user.id, now)
        assert self._count(db, user) == 0

    def test_no_deadline_task_no_notification(self, db, user):
        from src.database.models import Task, Priority, TaskStatus
        db.session.add(Task(user_id=user.id, title="No deadline",
                            priority=Priority.low, status=TaskStatus.pending))
        db.session.commit()
        self._sync(db, user.id)
        assert self._count(db, user) == 0

    def test_completed_task_gets_no_notification(self, db, user):
        now = datetime.now()
        _add_task(db, user, deadline=now - timedelta(hours=1), is_done=True)
        self._sync(db, user.id, now)
        assert self._count(db, user) == 0

    def test_completing_task_removes_existing_notification(self, db, user):
        now = datetime.now()
        t = _add_task(db, user, deadline=now - timedelta(hours=1))
        _add_notification(db, user, t, "OVERDUE")
        t.is_done = True
        db.session.commit()
        self._sync(db, user.id, now)
        assert self._count(db, user) == 0

    def test_overdue_replaces_reminder_on_deadline_pass(self, db, user):
        from src.database.models import Notification, NotificationType
        now = datetime.now()
        t = _add_task(db, user, deadline=now + timedelta(minutes=10), reminder_minutes=60)
        _add_notification(db, user, t, "REMINDER")
        self._sync(db, user.id, now + timedelta(hours=2))  # time passes
        assert Notification.query.filter_by(user_id=user.id, type=NotificationType.REMINDER).count() == 0
        assert Notification.query.filter_by(user_id=user.id, type=NotificationType.OVERDUE).count() == 1

    def test_repeated_sync_does_not_duplicate(self, db, user):
        now = datetime.now()
        _add_task(db, user, deadline=now - timedelta(hours=1))
        self._sync(db, user.id, now)
        self._sync(db, user.id, now)
        assert self._count(db, user) == 1

    def test_overdue_message_includes_days_count(self, db, user):
        from src.database.models import Notification, NotificationType
        now = datetime.now()
        _add_task(db, user, deadline=now - timedelta(days=3))
        self._sync(db, user.id, now)
        n = Notification.query.filter_by(user_id=user.id, type=NotificationType.OVERDUE).first()
        assert "3" in n.message

    def test_reminder_message_includes_reminder_minutes(self, db, user):
        from src.database.models import Notification, NotificationType
        now = datetime.now()
        _add_task(db, user, deadline=now + timedelta(minutes=20), reminder_minutes=60)
        self._sync(db, user.id, now)
        n = Notification.query.filter_by(user_id=user.id, type=NotificationType.REMINDER).first()
        assert "60" in n.message


class TestNotificationServiceOther:
    def test_get_notifications_empty(self, db, user):
        from src.services.notification_service import NotificationService
        assert NotificationService.get_notifications_for_user(user.id) == []

    def test_get_notifications_overdue_before_reminder(self, db, user, task, overdue_task):
        from src.services.notification_service import NotificationService
        _add_notification(db, user, task, "REMINDER")
        _add_notification(db, user, overdue_task, "OVERDUE")
        types = [str(n.type) for n in NotificationService.get_notifications_for_user(user.id)]
        assert types[0] == "OVERDUE"

    def test_mark_as_read_returns_true(self, db, user, notification):
        from src.services.notification_service import NotificationService
        assert NotificationService.mark_notification_as_read(notification.id, user.id) is True

    def test_mark_as_read_persists_to_db(self, db, user, notification):
        from src.database.models import Notification
        from src.services.notification_service import NotificationService
        NotificationService.mark_notification_as_read(notification.id, user.id)
        assert db.session.get(Notification, notification.id).is_read is True

    def test_mark_nonexistent_returns_false(self, db, user):
        from src.services.notification_service import NotificationService
        assert NotificationService.mark_notification_as_read(99999, user.id) is False

    def test_mark_other_users_notification_returns_false(self, db, user, other_user, notification):
        from src.services.notification_service import NotificationService
        assert NotificationService.mark_notification_as_read(notification.id, other_user.id) is False

    def test_mark_all_read_clears_unread_count(self, db, user, task):
        from src.database.models import Notification
        from src.services.notification_service import NotificationService
        _add_notification(db, user, task, "OVERDUE")
        _add_notification(db, user, task, "REMINDER")
        NotificationService.mark_all_notifications_as_read(user.id)
        assert Notification.query.filter_by(user_id=user.id, is_read=False).count() == 0

    def test_clear_returns_deleted_count(self, db, user, task):
        from src.services.notification_service import NotificationService
        _add_notification(db, user, task, "OVERDUE")
        _add_notification(db, user, task, "REMINDER")
        assert NotificationService.clear_all_notifications(user.id) == 2

    def test_clear_does_not_affect_other_users(self, db, user, other_user, task):
        from src.database.models import Notification, Task, Priority, TaskStatus
        from src.services.notification_service import NotificationService
        other_task = Task(user_id=other_user.id, title="T",
                          priority=Priority.low, status=TaskStatus.pending)
        db.session.add(other_task)
        db.session.commit()
        _add_notification(db, user, task, "OVERDUE")
        _add_notification(db, other_user, other_task, "OVERDUE")
        NotificationService.clear_all_notifications(user.id)
        assert Notification.query.filter_by(user_id=other_user.id).count() == 1
