from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Абстрактный базовый репозиторий.
    Определяет интерфейс для всех репозиториев в системе.
    
    Generic T - тип сущности, с которой работает репозиторий.
    """
    
    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Получить сущность по ID.
        
        Args:
            id: Идентификатор сущности
            
        Returns:
            Optional[T]: Найденная сущность или None
        """
        pass
    
    @abstractmethod
    def get_all(self, **filters) -> List[T]:
        """
        Получить все сущности с фильтрацией.
        
        Args:
            **filters: Параметры фильтрации
            
        Returns:
            List[T]: Список сущностей
        """
        pass
    
    @abstractmethod
    def add(self, entity: T) -> T:
        """
        Добавить новую сущность.
        
        Args:
            entity: Сущность для добавления
            
        Returns:
            T: Добавленная сущность с присвоенным ID
        """
        pass
    
    @abstractmethod
    def update(self, entity: T) -> T:
        """
        Обновить существующую сущность.
        
        Args:
            entity: Сущность с обновленными данными
            
        Returns:
            T: Обновленная сущность
            
        Raises:
            ValueError: Если сущность не найдена
        """
        pass
    
    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Удалить сущность по ID.
        
        Args:
            id: Идентификатор сущности для удаления
            
        Returns:
            bool: True если удаление успешно, False если сущность не найдена
        """
        pass