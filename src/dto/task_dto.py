from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TaskDTO:
    """Data Transfer Object for Task model"""
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: str = "medium"
    status: str = "pending"
    reminder_minutes: int = 0
    is_done: bool = False
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, task_model):
        """Create DTO from database model"""
        return cls(
            id=task_model.id,
            title=task_model.title,
            description=task_model.description,
            deadline=task_model.deadline,
            priority=task_model.priority,
            status=task_model.status,
            reminder_minutes=task_model.reminder_minutes,
            is_done=task_model.is_done,
            user_id=task_model.user_id,
            created_at=task_model.created_at
        )

    def to_dict(self):
        """Convert DTO to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority,
            'status': self.status,
            'reminder_minutes': self.reminder_minutes,
            'is_done': self.is_done,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class TaskCreateDTO:
    """DTO for creating new tasks"""
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None  # ISO format string
    priority: str = "medium"
    reminder_minutes: int = 0

@dataclass
class TaskUpdateDTO:
    """DTO for updating existing tasks"""
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[str] = None  # ISO format string
    priority: Optional[str] = None
    reminder_minutes: Optional[int] = None
