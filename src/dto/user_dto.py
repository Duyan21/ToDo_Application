from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.database.models import User


@dataclass(frozen=True)
class UserDTO:
    id: int
    name: str
    email: str
    created_at: datetime | None

    @classmethod
    def from_model(cls, user: User) -> UserDTO:
        return cls(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
        )

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    def to_dict(self) -> dict:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat() if self.created_at else None
        return d


@dataclass
class UserRegisterDTO:
    name: str
    email: str
    password: str = field(repr=False)

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.email = self.email.strip().lower()


@dataclass
class UserLoginDTO:
    email: str
    password: str = field(repr=False)

    def __post_init__(self) -> None:
        self.email = self.email.strip().lower()
