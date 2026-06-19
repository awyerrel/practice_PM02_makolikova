import pytest
from datetime import date, timedelta
from src.services.booking_service import BookingService
from src.dto.booking_dto import BookingCreateDTO
from src.domain.exceptions import (
    RoomNotFoundError,
    BookingConflictError,
    BookingNotFoundError,
    BookingStatusError,
    HotelRatingTooLowError,
    InvalidDatesError
)
from src.domain.models import BookingStatus, Room, Hotel  # ДОБАВЛЯЕМ Hotel


class TestBookingService:
    """Тесты для BookingService"""
    
    def test_create_booking_success(self, booking_service, sample_room):
        """Тест успешного создания бронирования на английском"""
        dto = BookingCreateDTO(
            room_id=sample_room.id,
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            locale="en"
        )
        
        result = booking_service.create(dto)
        
        assert result.id is not None
        assert result.room_id == sample_room.id
        assert result.guest_name == "John Doe"
        assert result.total_price > 0
        assert result.locale == "en"
        assert result.message is not None
    
    def test_create_booking_success_russian(self, booking_service, sample_room):
        """Тест успешного создания бронирования на русском"""
        dto = BookingCreateDTO(
            room_id=sample_room.id,
            guest_name="Иван Петров",
            guest_email="ivan@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            locale="ru"
        )
        
        result = booking_service.create(dto)
        
        assert result.id is not None
        assert result.locale == "ru"
        assert result.guest_name == "Иван Петров"
        assert "Бронирование" in result.message or "created" in result.message
    
    def test_create_booking_with_messages(self, booking_service, sample_room):
        """Тест создания бронирования с локализованными сообщениями"""
        dto = BookingCreateDTO(
            room_id=sample_room.id,
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            locale="en"
        )
        
        result = booking_service.create(dto)
        
        assert result.id is not None
        assert result.message is not None
        assert "created" in result.message.lower()
    
    def test_create_booking_room_not_found(self, booking_service):
        """Тест ошибки при создании бронирования для несуществующего номера"""
        dto = BookingCreateDTO(
            room_id=999,
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            locale="en"
        )
        
        with pytest.raises(RoomNotFoundError) as exc_info:
            booking_service.create(dto)
        
        assert "not found" in str(exc_info.value)
    
    def test_create_booking_conflict(self, booking_service, sample_room, sample_booking):
        """Тест ошибки конфликта бронирования"""
        dto = BookingCreateDTO(
            room_id=sample_room.id,
            guest_name="Jane Doe",
            guest_email="jane@example.com",
            check_in=date(2026, 6, 16),
            check_out=date(2026, 6, 18),
            locale="en"
        )
        
        with pytest.raises(BookingConflictError) as exc_info:
            booking_service.create(dto)
        
        assert "already booked" in str(exc_info.value)
    
    def test_create_booking_invalid_dates(self, booking_service, sample_room):
        """Тест ошибки при неверных датах (выезд раньше заезда)"""
        # Создаем DTO с неверными датами - ожидаем ValidationError от Pydantic
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            BookingCreateDTO(
                room_id=sample_room.id,
                guest_name="John Doe",
                guest_email="john@example.com",
                check_in=date(2026, 6, 20),
                check_out=date(2026, 6, 15),  # Выезд раньше заезда
                locale="en"
            )
        
        assert "check_out_must_be_after_check_in" in str(exc_info.value)
    
    def test_create_booking_long_stay(self, booking_service, sample_room):
        """Тест ошибки при слишком длительном бронировании (>30 дней)"""
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError) as exc_info:
            BookingCreateDTO(
                room_id=sample_room.id,
                guest_name="John Doe",
                guest_email="john@example.com",
                check_in=date(2026, 6, 1),
                check_out=date(2026, 7, 15),  # 44 дня > 30
                locale="en"
            )
        
        assert "booking_exceeds_max_duration" in str(exc_info.value)
    
    def test_cancel_booking_success(self, booking_service, sample_booking):
        """Тест успешной отмены бронирования"""
        result = booking_service.cancel(sample_booking.id, "en")
        
        assert result["success"] is True
        assert result["booking_id"] == sample_booking.id
        assert result["status"] == BookingStatus.CANCELLED.value
        assert "cancelled" in result["message"].lower()
    
    def test_cancel_booking_not_found(self, booking_service):
        """Тест ошибки при отмене несуществующего бронирования"""
        with pytest.raises(BookingNotFoundError) as exc_info:
            booking_service.cancel(999, "en")
        
        assert "not found" in str(exc_info.value)
    
    def test_confirm_booking_success(self, booking_service, sample_booking):
        """Тест успешного подтверждения бронирования"""
        result = booking_service.confirm(sample_booking.id, "en")
        
        assert result["success"] is True
        assert result["status"] == BookingStatus.CONFIRMED.value
        assert "confirmed" in result["message"].lower()
    
    def test_confirm_booking_already_confirmed(self, booking_service, sample_booking):
        """Тест ошибки подтверждения уже подтвержденного бронирования"""
        # Сначала подтверждаем
        booking_service.confirm(sample_booking.id, "en")
        
        # Пытаемся подтвердить еще раз
        with pytest.raises(BookingStatusError) as exc_info:
            booking_service.confirm(sample_booking.id, "en")
        
        assert "cannot be modified" in str(exc_info.value)
    
    def test_check_in_success(self, booking_service, sample_booking):
        """Тест успешного заезда"""
        # Сначала подтверждаем
        booking_service.confirm(sample_booking.id, "en")
        
        # Затем заезд
        result = booking_service.check_in(sample_booking.id, "en")
        
        assert result["success"] is True
        assert result["status"] == BookingStatus.CHECKED_IN.value
    
    def test_check_out_success(self, booking_service, sample_booking):
        """Тест успешного выезда"""
        # Подтверждаем и заезжаем
        booking_service.confirm(sample_booking.id, "en")
        booking_service.check_in(sample_booking.id, "en")
        
        # Выезд
        result = booking_service.check_out(sample_booking.id, "en")
        
        assert result["success"] is True
        assert result["status"] == BookingStatus.CHECKED_OUT.value
    
    def test_get_available_rooms(self, booking_service, sample_hotel, sample_room, sample_booking):
        """Тест поиска доступных номеров"""
        # Создаем еще один номер в том же отеле
        room2 = Room(
            id=None,
            hotel_id=sample_hotel.id,
            number="102",
            capacity=4,
            price_per_night=150.0,
            is_active=True
        )
        booking_service.uow.rooms.add(room2)
        
        # Ищем доступные номера на даты, пересекающиеся с существующим бронированием
        available = booking_service.get_available_rooms(
            sample_hotel.id,
            date(2026, 6, 16),
            date(2026, 6, 18),
            locale="en"
        )
        
        # Должен быть доступен только номер 102 (101 уже забронирован)
        assert len(available) == 1
        assert available[0]["room_id"] == room2.id
    
    def test_get_available_rooms_with_capacity_filter(self, booking_service, sample_hotel):
        """Тест поиска доступных номеров с фильтром по вместимости"""
        # Создаем номера с разной вместимостью
        room1 = Room(id=None, hotel_id=sample_hotel.id, number="101", capacity=2, price_per_night=100.0)
        room2 = Room(id=None, hotel_id=sample_hotel.id, number="102", capacity=4, price_per_night=150.0)
        
        booking_service.uow.rooms.add(room1)
        booking_service.uow.rooms.add(room2)
        
        available = booking_service.get_available_rooms(
            sample_hotel.id,
            date(2026, 7, 1),
            date(2026, 7, 5),
            capacity=3,
            locale="en"
        )
        
        # Должен быть доступен только номер с вместимостью 4
        assert len(available) == 1
        assert available[0]["capacity"] == 4
        assert available[0]["room_id"] == room2.id
    
    def test_hotel_rating_too_low(self, booking_service, uow):
        """Тест ошибки при низком рейтинге отеля"""
        # Создаем отель с низким рейтингом
        hotel = Hotel(
            id=None,
            name="Low Rating Hotel",
            address="456 Low St",
            phone="+1234567890",
            rating=2.5
        )
        uow.hotels.add(hotel)
        
        # Создаем номер в этом отеле
        room = Room(
            id=None,
            hotel_id=hotel.id,
            number="201",
            capacity=2,
            price_per_night=80.0
        )
        uow.rooms.add(room)
        
        dto = BookingCreateDTO(
            room_id=room.id,
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in=date(2026, 6, 15),
            check_out=date(2026, 6, 20),
            locale="en"
        )
        
        with pytest.raises(HotelRatingTooLowError) as exc_info:
            booking_service.create(dto)
        
        assert "rating" in str(exc_info.value)
    
    def test_get_by_id_success(self, booking_service, sample_booking):
        """Тест получения бронирования по ID"""
        result = booking_service.get_by_id(sample_booking.id, "en")
        
        assert result.id == sample_booking.id
        assert result.guest_name == sample_booking.guest_name
        assert result.status == sample_booking.status.value
    
    def test_get_by_id_not_found(self, booking_service):
        """Тест ошибки получения несуществующего бронирования"""
        with pytest.raises(BookingNotFoundError):
            booking_service.get_by_id(999, "en")
    
    def test_get_by_guest(self, booking_service, sample_booking):
        """Тест получения бронирований по email гостя"""
        results = booking_service.get_by_guest("john@example.com", "en")
        
        assert len(results) > 0
        assert results[0].guest_email == "john@example.com"
    
    def test_get_status_text(self, booking_service, sample_booking):
        """Тест получения текста статуса"""
        status_text = booking_service.get_status_text(sample_booking.id, "en")
        
        assert "pending" in status_text.lower() or "ожидает" in status_text