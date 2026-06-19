from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class BookingStatus(Enum):
    """Статусы бронирования"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


@dataclass
class Hotel:
    """Модель отеля"""
    id: Optional[int]
    name: str
    address: str
    phone: str
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if self.rating < 0 or self.rating > 5:
            raise ValueError("Rating must be between 0 and 5")
        if not self.name or not self.name.strip():
            raise ValueError("Hotel name cannot be empty")
        if not self.phone or not self.phone.strip():
            raise ValueError("Phone number cannot be empty")


@dataclass
class Room:
    """Модель номера"""
    id: Optional[int]
    hotel_id: int
    number: str
    capacity: int
    price_per_night: float
    is_active: bool = True
    room_type: str = "standard"  # standard, deluxe, suite
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if self.capacity < 1:
            raise ValueError("Capacity must be at least 1")
        if self.price_per_night <= 0:
            raise ValueError("Price per night must be greater than 0")
        if not self.number or not self.number.strip():
            raise ValueError("Room number cannot be empty")
        if self.hotel_id <= 0:
            raise ValueError("Hotel ID must be greater than 0")
        
        allowed_types = ["standard", "deluxe", "suite"]
        if self.room_type not in allowed_types:
            self.room_type = "standard"


@dataclass
class Booking:
    """Модель бронирования"""
    id: Optional[int]
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    total_price: float
    status: BookingStatus = BookingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    cancelled_at: Optional[datetime] = None
    locale: str = "en"  # Язык пользователя (en/ru)
    
    def __post_init__(self):
        """Валидация после инициализации"""
        if self.room_id <= 0:
            raise ValueError("Room ID must be greater than 0")
        if not self.guest_name or not self.guest_name.strip():
            raise ValueError("Guest name cannot be empty")
        if '@' not in self.guest_email or '.' not in self.guest_email:
            raise ValueError("Invalid email format")
        if self.check_out <= self.check_in:
            raise ValueError("Check-out date must be after check-in date")
        if (self.check_out - self.check_in).days > 30:
            raise ValueError("Booking cannot exceed 30 days")
        if self.total_price <= 0:
            raise ValueError("Total price must be greater than 0")
        if self.locale not in ["en", "ru"]:
            self.locale = "en"
    
    def cancel(self) -> None:
        """Отменить бронирование"""
        if self.status in (BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT):
            raise ValueError(f"Cannot cancel booking in status {self.status.value}")
        self.status = BookingStatus.CANCELLED
        self.cancelled_at = datetime.now()
    
    def confirm(self) -> None:
        """Подтвердить бронирование"""
        if self.status != BookingStatus.PENDING:
            raise ValueError(f"Cannot confirm booking in status {self.status.value}")
        self.status = BookingStatus.CONFIRMED
    
    def check_in_guest(self) -> None:
        """Отметить заезд гостя"""
        if self.status != BookingStatus.CONFIRMED:
            raise ValueError(f"Cannot check in booking in status {self.status.value}")
        self.status = BookingStatus.CHECKED_IN
    
    def check_out_guest(self) -> None:
        """Отметить выезд гостя"""
        if self.status != BookingStatus.CHECKED_IN:
            raise ValueError(f"Cannot check out booking in status {self.status.value}")
        self.status = BookingStatus.CHECKED_OUT
    
    def is_active(self) -> bool:
        """Проверить, активно ли бронирование"""
        return self.status not in (BookingStatus.CANCELLED, BookingStatus.CHECKED_OUT)
    
    def get_nights(self) -> int:
        """Получить количество ночей"""
        return (self.check_out - self.check_in).days
    
    def overlaps_with(self, other: 'Booking') -> bool:
        """Проверить пересечение с другим бронированием"""
        if self.room_id != other.room_id:
            return False
        if self.status == BookingStatus.CANCELLED or other.status == BookingStatus.CANCELLED:
            return False
        return self.check_in < other.check_out and self.check_out > other.check_in