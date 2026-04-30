from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserDTO:
    """Data Transfer Object for User model"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: Optional[str] = None
    created_at: Optional[datetime] = None
    is_active: bool = True

    @classmethod
    def from_model(cls, user_model):
        """Create DTO from database model"""
        return cls(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            password_hash=user_model.password_hash,
            created_at=user_model.created_at,
            is_active=user_model.is_active
        )

    def to_dict(self):
        """Convert DTO to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

@dataclass
class UserCreateDTO:
    """DTO for creating new users"""
    username: str
    email: str
    password: str

@dataclass
class UserLoginDTO:
    """DTO for user login"""
    username: str
    password: str

@dataclass
class UserUpdateDTO:
    """DTO for updating user profile"""
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
