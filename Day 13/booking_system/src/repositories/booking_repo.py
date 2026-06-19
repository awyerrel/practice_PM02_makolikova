from typing import List, Optional
from datetime import date
from src.domain.models import Booking, BookingStatus
from src.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Репозиторий для работы с бронированиями (In-Memory)"""
    
    def __init__(self):
        self._storage: dict[int, Booking] = {}
        self._next_id = 1
    
    def get_by_id(self, id: int) -> Optional[Booking]:
        """Получить бронирование по ID"""
        return self._storage.get(id)
    
    def get_all(self, **filters) -> List[Booking]:
        """Получить все бронирования с фильтрацией"""
        result = list(self._storage.values())
        
        if 'room_id' in filters:
            result = [b for b in result if b.room_id == filters['room_id']]
        
        if 'status' in filters:
            result = [b for b in result if b.status == filters['status']]
        
        if 'guest_email' in filters:
            result = [b for b in result if b.guest_email == filters['guest_email']]
        
        if 'locale' in filters:
            result = [b for b in result if b.locale == filters['locale']]
        
        if 'guest_name' in filters:
            result = [b for b in result if filters['guest_name'].lower() in b.guest_name.lower()]
        
        if 'check_in_after' in filters:
            result = [b for b in result if b.check_in >= filters['check_in_after']]
        
        if 'check_out_before' in filters:
            result = [b for b in result if b.check_out <= filters['check_out_before']]
        
        return result
    
    def add(self, booking: Booking) -> Booking:
        """Добавить новое бронирование"""
        booking.id = self._next_id
        self._storage[booking.id] = booking
        self._next_id += 1
        return booking
    
    def update(self, booking: Booking) -> Booking:
        """Обновить бронирование"""
        if booking.id not in self._storage:
            raise ValueError(f"Booking with id {booking.id} not found")
        self._storage[booking.id] = booking
        return booking
    
    def delete(self, id: int) -> bool:
        """Удалить бронирование"""
        if id in self._storage:
            del self._storage[id]
            return True
        return False
    
    def get_by_room_and_dates(
        self, 
        room_id: int, 
        check_in: date, 
        check_out: date
    ) -> List[Booking]:
        """
        Найти бронирования для номера в указанном диапазоне дат.
        Учитываются только активные бронирования (не отмененные).
        """
        result = []
        for booking in self._storage.values():
            if booking.room_id != room_id:
                continue
            if booking.status == BookingStatus.CANCELLED:
                continue
            # Проверка пересечения интервалов
            if booking.check_in < check_out and booking.check_out > check_in:
                result.append(booking)
        return result
    
    def get_active_for_room(self, room_id: int) -> List[Booking]:
        """Получить все активные бронирования для номера"""
        result = []
        for booking in self._storage.values():
            if booking.room_id != room_id:
                continue
            if booking.status not in [BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT]:
                result.append(booking)
        return result
    
    def get_by_guest(self, guest_email: str) -> List[Booking]:
        """Получить все бронирования гостя по email"""
        return self.get_all(guest_email=guest_email)
    
    def get_by_status(self, status: BookingStatus) -> List[Booking]:
        """Получить все бронирования по статусу"""
        return self.get_all(status=status)
    
    def get_pending_bookings(self) -> List[Booking]:
        """Получить все бронирования в статусе PENDING"""
        return self.get_by_status(BookingStatus.PENDING)
    
    def get_confirmed_bookings(self) -> List[Booking]:
        """Получить все бронирования в статусе CONFIRMED"""
        return self.get_by_status(BookingStatus.CONFIRMED)
    
    def get_cancelled_bookings(self) -> List[Booking]:
        """Получить все отмененные бронирования"""
        return self.get_by_status(BookingStatus.CANCELLED)
    
    def get_bookings_by_date_range(
        self, 
        start_date: date, 
        end_date: date
    ) -> List[Booking]:
        """Получить бронирования в диапазоне дат"""
        result = []
        for booking in self._storage.values():
            if (booking.check_in <= end_date and 
                booking.check_out >= start_date):
                result.append(booking)
        return result
    
    def get_booking_count_for_room(self, room_id: int) -> int:
        """Получить количество бронирований для номера"""
        return len(self.get_all(room_id=room_id))