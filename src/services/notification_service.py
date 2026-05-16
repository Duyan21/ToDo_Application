from datetime import datetime, timedelta
from src.database.models import db, Task, Notification, NotificationType

class NotificationService:
    @staticmethod
    def check_and_create_notifications():
        """Sync notifications with current task status using real-time joins"""
        try:
            users_with_tasks = db.session.query(Task.user_id).distinct().all()

            if not users_with_tasks:
                return

            now = datetime.now()
            for user_tuple in users_with_tasks:
                user_id = user_tuple[0]
                NotificationService._sync_notifications_for_user(user_id, now)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
    
    @staticmethod
    def _sync_notifications_for_user(user_id, now):
        """Sync notifications with current task status using optimized queries"""
        synced_count = 0
        
        # Get all current tasks for this user in one query
        current_tasks = Task.query.filter_by(user_id=user_id).all()
        
        # Create sets for quick lookups
        valid_task_ids = {task.id for task in current_tasks if not task.is_done}
        
        # Delete all notifications for invalid tasks in one query
        if valid_task_ids:
            invalid_notifications = Notification.query.filter(
                Notification.user_id == user_id,
                ~Notification.task_id.in_(valid_task_ids)
            ).all()
        else:
            invalid_notifications = Notification.query.filter_by(user_id=user_id).all()
        
        for notification in invalid_notifications:
            db.session.delete(notification)
            synced_count += 1
        
        # Get existing notifications for valid tasks in one query
        existing_notifications = {}
        if valid_task_ids:
            notifications = Notification.query.filter(
                Notification.user_id == user_id,
                Notification.task_id.in_(valid_task_ids)
            ).all()
            for notif in notifications:
                existing_notifications[notif.task_id] = notif
        
        # Process each valid task
        for task in current_tasks:
            if task.is_done:
                continue
                
            is_overdue = task.deadline and task.deadline < now
            should_remind = (not is_overdue and task.deadline and
                           task.reminder_minutes > 0 and
                           (task.deadline - timedelta(minutes=task.reminder_minutes)) <= now)
            
            # Determine what notification should exist
            if is_overdue:
                # Should only have OVERDUE notification
                existing = existing_notifications.get(task.id)
                
                # Remove any existing reminder
                if existing and existing.type == NotificationType.REMINDER:
                    db.session.delete(existing)
                    synced_count += 1
                    existing = None
                
                # Create or update overdue
                if not existing:
                    days_overdue = (now - task.deadline).days
                    notification = Notification(
                        task_id=task.id,
                        user_id=user_id,
                        type=NotificationType.OVERDUE,
                        message=f'Task "{task.title}" đã quá hạn {days_overdue} ngày',
                        notify_time=now
                    )
                    db.session.add(notification)
                    synced_count += 1
                    
            elif should_remind:
                # Should only have REMINDER notification
                existing = existing_notifications.get(task.id)
                
                # Remove any existing overdue
                if existing and existing.type == NotificationType.OVERDUE:
                    db.session.delete(existing)
                    synced_count += 1
                    existing = None
                
                # Create or update reminder
                if not existing:
                    notification = Notification(
                        task_id=task.id,
                        user_id=user_id,
                        type=NotificationType.REMINDER,
                        message=f'Task "{task.title}" sắp đến hạn trong {task.reminder_minutes} phút',
                        notify_time=now
                    )
                    db.session.add(notification)
                    synced_count += 1
                    
            else:
                # Should have no notification
                existing = existing_notifications.get(task.id)
                if existing:
                    db.session.delete(existing)
                    synced_count += 1
        
        return synced_count
