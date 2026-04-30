from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FileDTO:
    """Data Transfer Object for File model"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    file_type: str = ""  # JSON, CSV
    created_at: Optional[datetime] = None
    path: str = ""

    @classmethod
    def from_model(cls, file_model):
        """Create DTO from database model"""
        return cls(
            id=file_model.id,
            user_id=file_model.user_id,
            file_type=file_model.file_type,
            created_at=file_model.created_at,
            path=file_model.path
        )

    def to_dict(self):
        """Convert DTO to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'path': self.path
        }

@dataclass
class FileCreateDTO:
    """DTO for creating new file records"""
    user_id: int
    file_type: str  # JSON, CSV
    path: str

@dataclass
class FileUpdateDTO:
    """DTO for updating file records"""
    file_type: Optional[str] = None
    path: Optional[str] = None
