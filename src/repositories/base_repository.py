from abc import ABC, abstractmethod
from typing import Any


class AbstractRepository(ABC):
    """Abstract base repository defining CRUD operation signatures."""

    @abstractmethod
    def create(self, **kwargs: Any):
        pass

    @abstractmethod
    def get_by_id(self, entity_id: int):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def find(self, **filters: Any):
        pass

    @abstractmethod
    def first(self, **filters: Any):
        pass

    @abstractmethod
    def update(self, entity_id: int, **kwargs: Any):
        pass

    @abstractmethod
    def delete(self, entity_id: int):
        pass

    @abstractmethod
    def delete_all(self):
        pass

    @abstractmethod
    def custom_query(self, **kwargs: Any):
        pass
