from datetime import datetime, timedelta
from src.database.models import db, Task, Notification

class NotificationService:
    @staticmethod
    def check_and_create_notifications():
        """Sync notifications with current task status using real-time joins"""
        try:
            # Get all users with tasks in one query
            users_with_tasks = db.session.query(Task.user_id).distinct().all()
            
            if not users_with_tasks:
                return
                
            for user_tuple in users_with_tasks:
                user_id = user_tuple[0]
                NotificationService._sync_notifications_for_user(user_id)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
    
    @staticmethod
    def _create_notifications_for_user(user_id):
        """Create notifications for a specific user. Returns count of created notifications."""
        created_count = 0
        
        # Check overdue tasks
        overdue_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.deadline < datetime.now(),
            Task.is_done == False
        ).all()
        
        for task in overdue_tasks:
            # Check if notification already exists
            existing = Notification.query.filter_by(
                task_id=task.id,
                user_id=user_id,
                type='OVERDUE'
            ).first()
            
            if not existing:
                days_overdue = (datetime.now() - task.deadline).days
                message = f'Task "{task.title}" đã quá hạn {days_overdue} ngày'
                
                notification = Notification(
                    task_id=task.id,
                    user_id=user_id,
                    type='OVERDUE',
                    message=message,
                    notify_time=datetime.now()
                )
                db.session.add(notification)
                created_count += 1
        
        # Check reminder tasks
        reminder_tasks = Task.query.filter(
            Task.user_id == user_id,
            Task.deadline > datetime.now(),
            Task.is_done == False,
            Task.reminder_minutes > 0
        ).all()
        
        for task in reminder_tasks:
            reminder_time = task.deadline - timedelta(minutes=task.reminder_minutes)
            
            # Check if reminder should be sent now
            if reminder_time <= datetime.now():
                existing = Notification.query.filter_by(
                    task_id=task.id,
                    user_id=user_id,
                    type='REMINDER'
                ).first()
                
                if not existing:
                    message = f'Task "{task.title}" sắp đến hạn trong {task.reminder_minutes} phút'
                    
                    notification = Notification(
                        task_id=task.id,
                        user_id=user_id,
                        type='REMINDER',
                        message=message,
                        notify_time=datetime.now()
                    )
                    db.session.add(notification)
                    created_count += 1
        
        return created_count
    
    @staticmethod
    def _sync_notifications_for_user(user_id):
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
                
            is_overdue = task.deadline and task.deadline < datetime.now()
            should_remind = (not is_overdue and task.deadline and 
                           task.reminder_minutes > 0 and 
                           (task.deadline - timedelta(minutes=task.reminder_minutes)) <= datetime.now())
            
            # Determine what notification should exist
            if is_overdue:
                # Should only have OVERDUE notification
                existing = existing_notifications.get(task.id)
                
                # Remove any existing reminder
                if existing and existing.type == 'REMINDER':
                    db.session.delete(existing)
                    synced_count += 1
                    existing = None
                
                # Create or update overdue
                if not existing:
                    days_overdue = (datetime.now() - task.deadline).days
                    notification = Notification(
                        task_id=task.id,
                        user_id=user_id,
                        type='OVERDUE',
                        message=f'Task "{task.title}" đã quá hạn {days_overdue} ngày',
                        notify_time=datetime.now()
                    )
                    db.session.add(notification)
                    synced_count += 1
                    
            elif should_remind:
                # Should only have REMINDER notification
                existing = existing_notifications.get(task.id)
                
                # Remove any existing overdue
                if existing and existing.type == 'OVERDUE':
                    db.session.delete(existing)
                    synced_count += 1
                    existing = None
                
                # Create or update reminder
                if not existing:
                    notification = Notification(
                        task_id=task.id,
                        user_id=user_id,
                        type='REMINDER',
                        message=f'Task "{task.title}" sắp đến hạn trong {task.reminder_minutes} phút',
                        notify_time=datetime.now()
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
