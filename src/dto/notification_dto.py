from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class NotificationDTO:
    """Data Transfer Object for Notification model"""
    id: Optional[int] = None
    task_id: Optional[int] = None
    user_id: Optional[int] = None
    type: str = ""  # REMINDER, OVERDUE
    message: str = ""
    notify_time: Optional[datetime] = None
    sent: bool = False
    is_read: bool = False
    created_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, notification_model):
        """Create DTO from database model"""
        return cls(
            id=notification_model.id,
            task_id=notification_model.task_id,
            user_id=notification_model.user_id,
            type=notification_model.type,
            message=notification_model.message,
            notify_time=notification_model.notify_time,
            sent=notification_model.sent,
            is_read=notification_model.is_read,
            created_at=notification_model.created_at
        )

    def to_dict(self):
        """Convert DTO to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'type': self.type,
            'message': self.message,
            'notify_time': self.notify_time.isoformat() if self.notify_time else None,
            'sent': self.sent,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class NotificationCreateDTO:
    """DTO for creating new notifications"""
    task_id: int
    user_id: int
    type: str  # REMINDER, OVERDUE
    message: str
    notify_time: Optional[datetime] = None

@dataclass
class NotificationUpdateDTO:
    """DTO for updating notifications"""
    message: Optional[str] = None
    notify_time: Optional[datetime] = None
    sent: Optional[bool] = None
    is_read: Optional[bool] = None
