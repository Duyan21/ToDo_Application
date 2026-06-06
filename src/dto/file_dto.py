from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FileDTO:
    """Data Transfer Object for File model"""
    id: Optional[int] = None
    user_id: Optional[int] = None
    filename: str = ""
    file_path: str = ""
    is_imported: bool = False
    uploaded_at: Optional[datetime] = None

    @classmethod
    def from_model(cls, file_model):
        """Create DTO from database model"""
        return cls(
            id=file_model.id,
            user_id=file_model.user_id,
            filename=file_model.filename,
            file_path=file_model.file_path,
            is_imported=file_model.is_imported,
            uploaded_at=file_model.uploaded_at,
        )

    def to_dict(self):
        """Convert DTO to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'is_imported': self.is_imported,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
        }


@dataclass
class FileCreateDTO:
    """DTO for creating new file records"""
    user_id: int
    filename: str
    file_path: str


@dataclass
class FileUpdateDTO:
    """DTO for updating file records"""
    filename: Optional[str] = None
    file_path: Optional[str] = None
    is_imported: Optional[bool] = None
