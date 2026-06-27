# src/infrastructure/uow.py
"""
Unit of Work (UoW) паттерн для управления транзакциями

Обеспечивает:
- Атомарность операций
- Управление транзакциями
- Координацию между репозиториями
- Обработку ошибок и откат изменений
- Контекстное управление

Применяется для:
- Согласованности данных между репозиториями
- Группировки операций в одну транзакцию
- Упрощения тестирования
"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Type, Union, Callable
import logging
import traceback
from enum import Enum

from src.core.domain import (
    Location, Hotel, Route, RouteSegment, Coordinates
)
from src.core.exceptions import DomainError, ValidationError
from src.infrastructure.repositories import (
    InMemoryLocationRepository,
    InMemoryHotelRepository,
    InMemoryRouteRepository
)


# --- Настройка логирования ---
logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """Статус транзакции"""
    NOT_STARTED = "not_started"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    ERROR = "error"


@dataclass
class TransactionContext:
    """Контекст транзакции"""
    id: str = field(default_factory=lambda: f"txn_{datetime.now().timestamp()}")
    status: TransactionStatus = TransactionStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    operations: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[Exception] = None
    
    def start(self) -> None:
        """Начать транзакцию"""
        self.status = TransactionStatus.ACTIVE
        self.started_at = datetime.now()
        logger.debug(f"Transaction {self.id} started")
    
    def complete(self, success: bool = True) -> None:
        """Завершить транзакцию"""
        self.completed_at = datetime.now()
        if success:
            self.status = TransactionStatus.COMMITTED
            logger.debug(f"Transaction {self.id} committed")
        else:
            self.status = TransactionStatus.ROLLED_BACK
            logger.debug(f"Transaction {self.id} rolled back")
    
    def add_operation(self, operation_type: str, data: Dict[str, Any]) -> None:
        """Добавить операцию в транзакцию"""
        self.operations.append({
            'type': operation_type,
            'data': data,
            'timestamp': datetime.now()
        })
    
    def set_error(self, error: Exception) -> None:
        """Установить ошибку транзакции"""
        self.error = error
        self.status = TransactionStatus.ERROR
        logger.error(f"Transaction {self.id} error: {error}")
    
    @property
    def duration(self) -> Optional[float]:
        """Продолжительность транзакции в секундах"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_active(self) -> bool:
        """Активна ли транзакция"""
        return self.status == TransactionStatus.ACTIVE
    
    @property
    def is_successful(self) -> bool:
        """Успешно ли завершена транзакция"""
        return self.status == TransactionStatus.COMMITTED


class UnitOfWork(ABC):
    """
    Абстрактный Unit of Work
    
    Предоставляет интерфейс для управления транзакциями и репозиториями
    """
    
    def __init__(self):
        self._context = TransactionContext()
        self._repositories: Dict[str, Any] = {}
        self._on_commit_callbacks: List[Callable] = []
        self._on_rollback_callbacks: List[Callable] = []
    
    @abstractmethod
    def __enter__(self):
        """Вход в контекст"""
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Зафиксировать транзакцию"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Откатить транзакцию"""
        pass
    
    @abstractmethod
    def register_repository(self, name: str, repository) -> None:
        """Зарегистрировать репозиторий в UoW"""
        pass
    
    @abstractmethod
    def get_repository(self, name: str):
        """Получить репозиторий"""
        pass
    
    def add_on_commit(self, callback: Callable) -> None:
        """Добавить callback при успешной фиксации"""
        self._on_commit_callbacks.append(callback)
    
    def add_on_rollback(self, callback: Callable) -> None:
        """Добавить callback при откате"""
        self._on_rollback_callbacks.append(callback)
    
    def _execute_commit_callbacks(self) -> None:
        """Выполнить callbacks при фиксации"""
        for callback in self._on_commit_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in commit callback: {e}")
    
    def _execute_rollback_callbacks(self) -> None:
        """Выполнить callbacks при откате"""
        for callback in self._on_rollback_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in rollback callback: {e}")


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory реализация Unit of Work
    
    Использует in-memory репозитории и имитирует транзакции
    """
    
    def __init__(self):
        super().__init__()
        self._repositories = {}
        self._backup: Dict[str, Any] = {}
        self._committed = False
        self._rolled_back = False
        
        # Регистрируем репозитории по умолчанию
        self.register_repository('location', InMemoryLocationRepository())
        self.register_repository('hotel', InMemoryHotelRepository())
        self.register_repository('route', InMemoryRouteRepository())
    
    def __enter__(self):
        """Вход в контекст"""
        self._context.start()
        # Создаем бэкап репозиториев
        self._create_backup()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекста"""
        if exc_type is not None:
            # Произошло исключение - откатываем
            logger.error(f"Exception in transaction: {exc_val}")
            self.rollback()
            # Пробрасываем исключение дальше
            return False
        else:
            # Все хорошо - фиксируем
            self.commit()
            return True
    
    def _create_backup(self) -> None:
        """Создать бэкап текущего состояния"""
        self._backup = {}
        for name, repo in self._repositories.items():
            if hasattr(repo, '_locations'):
                self._backup[f'{name}_locations'] = repo._locations.copy()
                self._backup[f'{name}_next_id'] = repo._next_id
            elif hasattr(repo, '_hotels'):
                self._backup[f'{name}_hotels'] = repo._hotels.copy()
                self._backup[f'{name}_next_id'] = repo._next_id
            elif hasattr(repo, '_routes'):
                self._backup[f'{name}_routes'] = repo._routes.copy()
                self._backup[f'{name}_next_id'] = repo._next_id
    
    def _restore_backup(self) -> None:
        """Восстановить состояние из бэкапа"""
        for name, repo in self._repositories.items():
            if hasattr(repo, '_locations'):
                repo._locations = self._backup.get(f'{name}_locations', {}).copy()
                repo._next_id = self._backup.get(f'{name}_next_id', 1)
            elif hasattr(repo, '_hotels'):
                repo._hotels = self._backup.get(f'{name}_hotels', {}).copy()
                repo._next_id = self._backup.get(f'{name}_next_id', 1)
            elif hasattr(repo, '_routes'):
                repo._routes = self._backup.get(f'{name}_routes', {}).copy()
                repo._next_id = self._backup.get(f'{name}_next_id', 1)
    
    def commit(self) -> None:
        """Зафиксировать транзакцию"""
        if self._committed:
            logger.warning("Transaction already committed")
            return
        
        if self._rolled_back:
            raise DomainError("Cannot commit after rollback")
        
        try:
            # Проверяем целостность данных
            self._validate_data_integrity()
            
            # Выполняем commit callbacks
            self._execute_commit_callbacks()
            
            # Очищаем бэкап
            self._backup.clear()
            self._committed = True
            
            # Завершаем транзакцию
            self._context.complete(success=True)
            logger.info(f"Transaction {self._context.id} committed successfully")
            
        except Exception as e:
            logger.error(f"Error during commit: {e}")
            self._context.set_error(e)
            raise
    
    def rollback(self) -> None:
        """Откатить транзакцию"""
        if self._rolled_back:
            logger.warning("Transaction already rolled back")
            return
        
        if self._committed:
            raise DomainError("Cannot rollback after commit")
        
        try:
            # Восстанавливаем состояние из бэкапа
            self._restore_backup()
            
            # Выполняем rollback callbacks
            self._execute_rollback_callbacks()
            
            # Очищаем бэкап
            self._backup.clear()
            self._rolled_back = True
            
            # Завершаем транзакцию
            self._context.complete(success=False)
            logger.info(f"Transaction {self._context.id} rolled back")
            
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            self._context.set_error(e)
            raise
    
    def _validate_data_integrity(self) -> None:
        """Проверить целостность данных перед фиксацией"""
        # Проверяем, что все ссылки на локации существуют
        hotel_repo = self.get_repository('hotel')
        location_repo = self.get_repository('location')
        
        for hotel in hotel_repo._hotels.values():
            if hotel.location and hotel.location.id:
                # Проверяем, что локация существует
                if not location_repo.get_by_id(hotel.location.id):
                    raise ValidationError(
                        f"Hotel {hotel.id} references non-existent location {hotel.location.id}"
                    )
        
        # Проверяем маршруты
        route_repo = self.get_repository('route')
        for route in route_repo._routes.values():
            for segment in route.segments:
                if segment.start.id and not location_repo.get_by_id(segment.start.id):
                    raise ValidationError(
                        f"Route {route.id} references non-existent location {segment.start.id}"
                    )
                if segment.end.id and not location_repo.get_by_id(segment.end.id):
                    raise ValidationError(
                        f"Route {route.id} references non-existent location {segment.end.id}"
                    )
    
    def register_repository(self, name: str, repository) -> None:
        """Зарегистрировать репозиторий"""
        if name in self._repositories:
            logger.warning(f"Repository {name} already registered, overwriting")
        self._repositories[name] = repository
    
    def get_repository(self, name: str):
        """Получить репозиторий"""
        if name not in self._repositories:
            raise ValueError(f"Repository {name} not registered")
        return self._repositories[name]
    
    @property
    def context(self) -> TransactionContext:
        """Получить контекст транзакции"""
        return self._context
    
    @property
    def is_active(self) -> bool:
        """Активна ли транзакция"""
        return self._context.is_active
    
    @property
    def is_successful(self) -> bool:
        """Успешно ли завершена транзакция"""
        return self._context.is_successful


class UnitOfWorkFactory:
    """
    Фабрика для создания Unit of Work
    
    Используется для создания UoW с различными конфигурациями
    """
    
    @staticmethod
    def create_in_memory() -> InMemoryUnitOfWork:
        """Создать in-memory UoW"""
        return InMemoryUnitOfWork()
    
    @staticmethod
    @contextmanager
    def transaction(uow_type: str = 'in_memory'):
        """
        Контекстный менеджер для транзакций
        
        Example:
            with UnitOfWorkFactory.transaction() as uow:
                hotel_repo = uow.get_repository('hotel')
                hotel_repo.save(hotel)
                # Автоматически зафиксируется при выходе
        """
        if uow_type == 'in_memory':
            uow = InMemoryUnitOfWork()
        else:
            raise ValueError(f"Unknown UoW type: {uow_type}")
        
        with uow:
            yield uow


class UnitOfWorkManager:
    """
    Менеджер Unit of Work
    
    Управляет жизненным циклом UoW и обеспечивает
    корректную работу с несколькими транзакциями
    """
    
    def __init__(self):
        self._current_uow: Optional[UnitOfWork] = None
        self._uow_stack: List[UnitOfWork] = []
    
    def begin(self, uow_type: str = 'in_memory') -> UnitOfWork:
        """
        Начать новую транзакцию
        
        Args:
            uow_type: Тип UoW ('in_memory', 'sqlalchemy', etc.)
        
        Returns:
            UnitOfWork: Новый экземпляр UoW
        """
        if self._current_uow and self._current_uow.is_active:
            raise DomainError("Cannot start new transaction while one is active")
        
        if uow_type == 'in_memory':
            uow = InMemoryUnitOfWork()
        else:
            raise ValueError(f"Unknown UoW type: {uow_type}")
        
        self._uow_stack.append(uow)
        self._current_uow = uow
        return uow
    
    def commit(self) -> None:
        """Зафиксировать текущую транзакцию"""
        if not self._current_uow:
            raise DomainError("No active transaction to commit")
        self._current_uow.commit()
        self._uow_stack.pop()
        self._current_uow = self._uow_stack[-1] if self._uow_stack else None
    
    def rollback(self) -> None:
        """Откатить текущую транзакцию"""
        if not self._current_uow:
            raise DomainError("No active transaction to rollback")
        self._current_uow.rollback()
        self._uow_stack.pop()
        self._current_uow = self._uow_stack[-1] if self._uow_stack else None
    
    @contextmanager
    def transaction(self, uow_type: str = 'in_memory'):
        """
        Контекстный менеджер для транзакций
        
        Example:
            with uow_manager.transaction() as uow:
                # Выполняем операции
                uow.get_repository('hotel').save(hotel)
        """
        uow = self.begin(uow_type)
        try:
            yield uow
            self.commit()
        except Exception:
            self.rollback()
            raise
    
    @property
    def current_uow(self) -> Optional[UnitOfWork]:
        """Получить текущий UoW"""
        return self._current_uow
    
    @property
    def is_active(self) -> bool:
        """Есть ли активная транзакция"""
        return self._current_uow is not None and self._current_uow.is_active


# --- Декоратор для транзакций ---

def transactional(uow_manager: Optional[UnitOfWorkManager] = None):
    """
    Декоратор для автоматического управления транзакциями
    
    Args:
        uow_manager: Менеджер UoW (если None, создается новый)
    
    Example:
        @transactional()
        def create_hotel_with_location(hotel_data, location_data):
            # Все операции будут выполнены в одной транзакции
            location = location_repo.save(location_data)
            hotel.location = location
            hotel_repo.save(hotel)
            return hotel
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = uow_manager or UnitOfWorkManager()
            with manager.transaction() as uow:
                # Передаем uow в функцию через kwargs
                kwargs['_uow'] = uow
                result = func(*args, **kwargs)
                return result
        return wrapper
    return decorator


# --- Примеры использования ---

def example_usage():
    """Пример использования Unit of Work"""
    
    print("="*50)
    print("Пример использования Unit of Work")
    print("="*50)
    
    # 1. Базовое использование с контекстным менеджером
    print("\n1. Базовое использование:")
    with InMemoryUnitOfWork() as uow:
        location_repo = uow.get_repository('location')
        hotel_repo = uow.get_repository('hotel')
        route_repo = uow.get_repository('route')
        
        # Создаем локацию
        location = Location(
            name="Москва",
            coordinates=Coordinates(55.7558, 37.6173)
        )
        location = location_repo.save(location)
        print(f"  Создана локация: {location.name} (ID: {location.id})")
        
        # Создаем отель
        hotel = Hotel(
            name="Grand Hotel",
            location=location,
            rating=4.9
        )
        hotel = hotel_repo.save(hotel)
        print(f"  Создан отель: {hotel.name} (ID: {hotel.id})")
        
        # Создаем маршрут
        spb = Location(
            name="Санкт-Петербург",
            coordinates=Coordinates(59.9343, 30.3351)
        )
        spb = location_repo.save(spb)
        
        route = Route(segments=[
            RouteSegment(location, spb, TransportType.CAR)
        ])
        route.calculate_totals()
        route = route_repo.save(route)
        print(f"  Создан маршрут (ID: {route.id}, Дистанция: {route.total_distance:.0f} км)")
    
    print("  ✅ Транзакция успешно зафиксирована")
    
    # 2. Использование с откатом
    print("\n2. Использование с откатом:")
    try:
        with InMemoryUnitOfWork() as uow:
            hotel_repo = uow.get_repository('hotel')
            
            # Создаем отель
            hotel = Hotel(name="Отель для отката")
            hotel = hotel_repo.save(hotel)
            print(f"  Создан отель: {hotel.name} (ID: {hotel.id})")
            
            # Имитируем ошибку
            raise ValidationError("Ошибка валидации!")
            
    except ValidationError as e:
        print(f"  ❌ Произошла ошибка: {e}")
        print("  ✅ Транзакция откачена")
    
    # 3. Использование с UnitOfWorkManager
    print("\n3. Использование с UnitOfWorkManager:")
    manager = UnitOfWorkManager()
    
    with manager.transaction() as uow:
        location_repo = uow.get_repository('location')
        
        # Создаем несколько локаций
        cities = [
            ("Екатеринбург", 56.8389, 60.6057),
            ("Казань", 55.7887, 49.1221),
            ("Новосибирск", 55.0084, 82.9357)
        ]
        
        for name, lat, lon in cities:
            location = Location(
                name=name,
                coordinates=Coordinates(lat, lon)
            )
            location = location_repo.save(location)
            print(f"  Создана локация: {location.name} (ID: {location.id})")
    
    print("  ✅ Транзакция успешно зафиксирована")
    
    # 4. Использование декоратора
    print("\n4. Использование декоратора @transactional:")
    
    @transactional()
    def create_hotel_chain(hotels_data: List[Dict[str, Any]], _uow=None):
        """Создать цепочку отелей в одной транзакции"""
        location_repo = _uow.get_repository('location')
        hotel_repo = _uow.get_repository('hotel')
        
        created_hotels = []
        for data in hotels_data:
            # Создаем локацию
            location = Location(
                name=f"Локация {data['name']}",
                coordinates=Coordinates(data['lat'], data['lon'])
            )
            location = location_repo.save(location)
            
            # Создаем отель
            hotel = Hotel(
                name=data['name'],
                location=location,
                rating=data.get('rating', 4.0)
            )
            hotel = hotel_repo.save(hotel)
            created_hotels.append(hotel)
            print(f"  Создан отель: {hotel.name}")
        
        return created_hotels
    
    hotels_data = [
        {'name': 'Отель А', 'lat': 55.7558, 'lon': 37.6173, 'rating': 4.8},
        {'name': 'Отель Б', 'lat': 55.7658, 'lon': 37.6273, 'rating': 4.2},
        {'name': 'Отель В', 'lat': 55.7458, 'lon': 37.6073, 'rating': 4.5},
    ]
    
    hotels = create_hotel_chain(hotels_data)
    print(f"  ✅ Создано {len(hotels)} отелей в одной транзакции")
    
    # 5. Просмотр контекста транзакции
    print("\n5. Информация о последней транзакции:")
    with InMemoryUnitOfWork() as uow:
        location_repo = uow.get_repository('location')
        loc = Location(name="Тестовая")
        loc = location_repo.save(loc)
        
        print(f"  ID транзакции: {uow.context.id}")
        print(f"  Статус: {uow.context.status.value}")
        print(f"  Операций: {len(uow.context.operations)}")
    
    print("\n" + "="*50)
    print("Пример завершен")
    print("="*50)


# Для импорта TransportType в примере
from src.core.domain import TransportType


if __name__ == "__main__":
    example_usage()