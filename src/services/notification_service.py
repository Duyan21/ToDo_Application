from datetime import datetime, timedelta
from src.repositories import get_notification_repository, get_task_repository
from src.database.models import Notification, NotificationType


class NotificationService:
    @staticmethod
    def check_and_create_notifications():
        """Sync notifications with current task status using real-time joins"""
        try:
            task_repository = get_task_repository()
            users_with_tasks = task_repository.get_users_with_tasks()
            print(f"Users with tasks: {users_with_tasks}")
            if not users_with_tasks:
                return

            now = datetime.now()
            for user_id in users_with_tasks:
                NotificationService._sync_notifications_for_user(user_id, now)

        except Exception as e:
            raise e

    @staticmethod
    def _sync_notifications_for_user(user_id, now):
        """Sync notifications with current task status using optimized queries"""
        synced_count = 0

        task_repository = get_task_repository()
        notification_repository = get_notification_repository()

        # Get all current tasks for this user in one query
        current_tasks = task_repository.get_by_user(user_id)

        # Create sets for quick lookups
        valid_task_ids = {task.id for task in current_tasks if not task.is_done}

        # Find notifications for invalid or completed tasks and delete them
        notifications = notification_repository.find(user_id=user_id)
        invalid_notifications = (
            [
                notification
                for notification in notifications
                if notification.task_id not in valid_task_ids
            ]
            if valid_task_ids
            else notifications
        )

        for notification in invalid_notifications:
            notification_repository.delete(notification.id)
            synced_count += 1

        # Get existing notifications for valid tasks in one query
        existing_notifications = {}
        if valid_task_ids:
            notifications = notification_repository.find(
                user_id=user_id, task_id=valid_task_ids
            )
            for notif in notifications:
                existing_notifications[notif.task_id] = notif

        # Process each valid task
        for task in current_tasks:
            if task.is_done:
                continue

            is_overdue = task.deadline and task.deadline < now
            should_remind = (
                not is_overdue
                and task.deadline
                and task.reminder_minutes > 0
                and (task.deadline - timedelta(minutes=task.reminder_minutes)) <= now
            )

            # Determine what notification should exist
            if is_overdue:
                # Should only have OVERDUE notification
                existing = existing_notifications.get(task.id)

                # Remove any existing reminder
                if existing and existing.type == NotificationType.REMINDER:
                    notification_repository.delete(existing.id)
                    synced_count += 1
                    existing = None

                # Create or update overdue
                if not existing:
                    days_overdue = (now - task.deadline).days
                    notification_repository.create(
                        task_id=task.id,
                        user_id=user_id,
                        type=NotificationType.OVERDUE,
                        message=f'Task "{task.title}" đã quá hạn {days_overdue} ngày',
                        notify_time=now,
                    )
                    synced_count += 1

            elif should_remind:
                # Should only have REMINDER notification
                existing = existing_notifications.get(task.id)

                # Remove any existing overdue
                if existing and existing.type == NotificationType.OVERDUE:
                    notification_repository.delete(existing.id)
                    synced_count += 1
                    existing = None

                # Create or update reminder
                if not existing:
                    notification_repository.create(
                        task_id=task.id,
                        user_id=user_id,
                        type=NotificationType.REMINDER,
                        message=f'Task "{task.title}" sắp đến hạn trong {task.reminder_minutes} phút',
                        notify_time=now,
                    )
                    synced_count += 1

            else:
                # Should have no notification
                existing = existing_notifications.get(task.id)
                if existing:
                    notification_repository.delete(existing.id)
                    synced_count += 1

        return synced_count

    @staticmethod
    def get_notifications_for_user(user_id):
        """Get all notifications for a user, sorted by type and created_at"""
        notification_repository = get_notification_repository()
        notifications = notification_repository.find(
            user_id=user_id,
            order_by=[
                (Notification.type, "asc"),  # OVERDUE first, then REMINDER
                (Notification.created_at, "desc"),
            ],
        )
        return notifications

    @staticmethod
    def mark_notification_as_read(notification_id, user_id):
        notification_repository = get_notification_repository()
        notification = notification_repository.get_by_id(notification_id)

        if not notification or notification.user_id != user_id:
            return False

        notification_repository.update(notification.id, is_read=True)
        return True

    @staticmethod
    def mark_all_notifications_as_read(user_id):
        notification_repository = get_notification_repository()
        notifications = notification_repository.find(user_id=user_id, is_read=False)

        for notification in notifications:
            notification_repository.update(notification.id, is_read=True)

    @staticmethod
    def clear_all_notifications(user_id) -> int:
        notification_repository = get_notification_repository()
        deleted_count = notification_repository.delete_by_user_id(user_id)
        return deleted_count
