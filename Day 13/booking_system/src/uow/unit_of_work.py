from contextlib import contextmanager
from typing import Type, Optional
from src.repositories.booking_repo import BookingRepository
from src.repositories.hotel_repo import HotelRepository
from src.repositories.room_repo import RoomRepository


class UnitOfWork:
    """
    Unit of Work - паттерн для управления транзакциями.
    Обеспечивает транзакционную целостность операций с базой данных.
    
    Использование:
        with UnitOfWork() as uow:
            hotel = uow.hotels.add(hotel)
            room = uow.rooms.add(room)
            uow.commit()
    """
    
    def __init__(self):
        """Инициализация Unit of Work с репозиториями In-Memory"""
        self._hotel_repo = HotelRepository()
        self._room_repo = RoomRepository()
        self._booking_repo = BookingRepository()
        self._committed = False
        self._rolled_back = False
    
    @property
    def hotels(self) -> HotelRepository:
        """Получить репозиторий отелей"""
        return self._hotel_repo
    
    @property
    def rooms(self) -> RoomRepository:
        """Получить репозиторий номеров"""
        return self._room_repo
    
    @property
    def bookings(self) -> BookingRepository:
        """Получить репозиторий бронирований"""
        return self._booking_repo
    
    def commit(self) -> None:
        """
        Фиксация транзакции.
        В реальной БД здесь был бы session.commit()
        """
        if self._rolled_back:
            raise RuntimeError("Cannot commit after rollback")
        self._committed = True
    
    def rollback(self) -> None:
        """
        Откат транзакции.
        В реальной БД здесь был бы session.rollback()
        """
        self._rolled_back = True
        self._committed = False
    
    def is_committed(self) -> bool:
        """Проверить, зафиксирована ли транзакция"""
        return self._committed
    
    def is_rolled_back(self) -> bool:
        """Проверить, выполнен ли откат"""
        return self._rolled_back
    
    def reset(self) -> None:
        """
        Сбросить состояние UoW.
        Используется для очистки состояния между тестами.
        """
        self._committed = False
        self._rolled_back = False
    
    @contextmanager
    def __enter__(self):
        """Вход в контекстный менеджер"""
        self.reset()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Выход из контекстного менеджера.
        Если произошло исключение - откат, иначе - коммит.
        """
        if exc_type is not None:
            self.rollback()
        elif not self._committed and not self._rolled_back:
            self.commit()


class UnitOfWorkFactory:
    """
    Фабрика для создания Unit of Work.
    Позволяет создавать экземпляры UoW с разными репозиториями.
    """
    
    @staticmethod
    def create() -> UnitOfWork:
        """Создать стандартный Unit of Work"""
        return UnitOfWork()
    
    @staticmethod
    def create_with_clean_state() -> UnitOfWork:
        """Создать Unit of Work с чистыми репозиториями"""
        uow = UnitOfWork()
        uow.reset()
        return uow