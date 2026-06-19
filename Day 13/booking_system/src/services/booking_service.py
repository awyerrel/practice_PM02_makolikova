from datetime import date, datetime
from typing import List, Optional, Dict, Any
from src.domain.models import Booking, BookingStatus
from src.domain.exceptions import (
    RoomNotFoundError,
    BookingNotFoundError,
    BookingConflictError,
    InvalidDatesError,
    BookingStatusError,
    HotelNotFoundError,
    HotelRatingTooLowError
)
from src.dto.booking_dto import (
    BookingCreateDTO,
    BookingResponseDTO,
    BookingUpdateDTO
)
from src.uow.unit_of_work import UnitOfWork
from src.services.pricing_service import PricingService


class BookingService:
    """
    Сервис для управления бронированиями с поддержкой мультиязычности.
    Вариант 10: Мультиязычность (Internationalization + Factory)
    """
    
    def __init__(
        self,
        uow: UnitOfWork,
        pricing_service: PricingService,
        min_hotel_rating: float = 3.0
    ):
        """
        Инициализация сервиса бронирований.
        
        Args:
            uow: Unit of Work
            pricing_service: Сервис расчета стоимости
            min_hotel_rating: Минимальный рейтинг отеля для бронирования
        """
        self.uow = uow
        self.pricing_service = pricing_service
        self.booking_repo = uow.bookings
        self.room_repo = uow.rooms
        self.hotel_repo = uow.hotels
        self.min_hotel_rating = min_hotel_rating
    
    def _get_localized_message(self, key: str, params: dict, locale: str = "en") -> str:
        """
        Получить локализованное сообщение.
        Factory Pattern для создания сообщений.
        
        Args:
            key: Ключ сообщения
            params: Параметры для подстановки
            locale: Язык (en/ru)
            
        Returns:
            str: Локализованное сообщение
        """
        messages = {
            "booking.created": {
                "en": "Booking {booking_id} has been created successfully",
                "ru": "Бронирование {booking_id} успешно создано"
            },
            "booking.cancelled": {
                "en": "Booking {booking_id} has been cancelled",
                "ru": "Бронирование {booking_id} отменено"
            },
            "booking.confirmed": {
                "en": "Booking {booking_id} has been confirmed",
                "ru": "Бронирование {booking_id} подтверждено"
            },
            "booking.status.pending": {
                "en": "Booking {booking_id} is pending confirmation",
                "ru": "Бронирование {booking_id} ожидает подтверждения"
            },
            "booking.status.confirmed": {
                "en": "Booking {booking_id} is confirmed",
                "ru": "Бронирование {booking_id} подтверждено"
            },
            "booking.status.checked_in": {
                "en": "Booking {booking_id} is checked in",
                "ru": "Бронирование {booking_id} активно (заезд)"
            },
            "booking.status.checked_out": {
                "en": "Booking {booking_id} is checked out",
                "ru": "Бронирование {booking_id} завершено (выезд)"
            },
            "booking.status.cancelled": {
                "en": "Booking {booking_id} is cancelled",
                "ru": "Бронирование {booking_id} отменено"
            }
        }
        
        template = messages.get(key, {}).get(locale, messages.get(key, {}).get("en", key))
        try:
            return template.format(**params)
        except KeyError:
            return template
    
    def _get_status_message(self, booking_id: int, status: BookingStatus, locale: str = "en") -> str:
        """Получить локализованное сообщение о статусе"""
        return self._get_localized_message(
            f"booking.status.{status.value}",
            {"booking_id": booking_id},
            locale
        )
    
    def create(self, dto: BookingCreateDTO) -> BookingResponseDTO:
        """
        Создать новое бронирование с локализованными сообщениями.
        
        Args:
            dto: Данные для создания бронирования
            
        Returns:
            BookingResponseDTO: Созданное бронирование
            
        Raises:
            RoomNotFoundError: Если номер не найден
            HotelNotFoundError: Если отель не найден
            HotelRatingTooLowError: Если рейтинг отеля ниже минимального
            BookingConflictError: Если номер уже забронирован
            InvalidDatesError: Если даты неверные
        """
        locale = dto.locale
        
        # 1. Проверяем существование номера
        room = self.room_repo.get_by_id(dto.room_id)
        if not room:
            raise RoomNotFoundError(dto.room_id, locale)
        
        if not room.is_active:
            raise RoomNotFoundError(dto.room_id, locale)
        
        # 2. Проверяем существование отеля и его рейтинг
        hotel = self.hotel_repo.get_by_id(room.hotel_id)
        if not hotel:
            raise HotelNotFoundError(room.hotel_id, locale)
        
        if hotel.rating < self.min_hotel_rating:
            raise HotelRatingTooLowError(
                room.hotel_id, hotel.rating, self.min_hotel_rating, locale
            )
        
        # 3. Проверяем пересечения бронирований
        existing = self.booking_repo.get_by_room_and_dates(
            dto.room_id, dto.check_in, dto.check_out
        )
        if existing:
            raise BookingConflictError(
                dto.room_id,
                dto.check_in.isoformat(),
                dto.check_out.isoformat(),
                locale
            )
        
        # 4. Проверяем длительность бронирования
        nights = (dto.check_out - dto.check_in).days
        if nights < 1:
            raise InvalidDatesError(
                self._get_localized_message(
                    "dates.min_stay",
                    {"min_days": 1},
                    locale
                ),
                locale
            )
        if nights > 30:
            raise InvalidDatesError(
                self._get_localized_message(
                    "dates.max_stay",
                    {"max_days": 30},
                    locale
                ),
                locale
            )
        
        # 5. Рассчитываем стоимость
        total_price = self.pricing_service.calculate_price(
            room, dto.check_in, dto.check_out
        )
        
        # 6. Создаем бронирование
        booking = Booking(
            id=None,
            room_id=dto.room_id,
            guest_name=dto.guest_name,
            guest_email=dto.guest_email,
            check_in=dto.check_in,
            check_out=dto.check_out,
            total_price=total_price,
            status=BookingStatus.PENDING,
            locale=locale
        )
        
        # 7. Сохраняем
        saved = self.booking_repo.add(booking)
        self.uow.commit()
        
        # 8. Формируем локализованное сообщение
        message = self._get_localized_message(
            "booking.created",
            {"booking_id": saved.id},
            locale
        )
        
        return BookingResponseDTO.from_booking(saved, locale, message)
    
    def cancel(self, booking_id: int, locale: str = "en") -> Dict[str, Any]:
        """
        Отменить бронирование с локализованными сообщениями.
        
        Args:
            booking_id: ID бронирования
            locale: Язык для сообщений
            
        Returns:
            Dict: Результат операции с сообщением
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
            BookingStatusError: Если бронирование нельзя отменить
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        
        if booking.status in (BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT):
            raise BookingStatusError(booking_id, booking.status.value, locale)
        
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now()
        
        self.booking_repo.update(booking)
        self.uow.commit()
        
        message = self._get_localized_message(
            "booking.cancelled",
            {"booking_id": booking_id},
            locale
        )
        
        return {
            "success": True,
            "message": message,
            "booking_id": booking_id,
            "status": booking.status.value
        }
    
    def confirm(self, booking_id: int, locale: str = "en") -> Dict[str, Any]:
        """
        Подтвердить бронирование с локализованными сообщениями.
        
        Args:
            booking_id: ID бронирования
            locale: Язык для сообщений
            
        Returns:
            Dict: Результат операции с сообщением
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
            BookingStatusError: Если бронирование нельзя подтвердить
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        
        if booking.status != BookingStatus.PENDING:
            raise BookingStatusError(booking_id, booking.status.value, locale)
        
        booking.status = BookingStatus.CONFIRMED
        
        self.booking_repo.update(booking)
        self.uow.commit()
        
        message = self._get_localized_message(
            "booking.confirmed",
            {"booking_id": booking_id},
            locale
        )
        
        return {
            "success": True,
            "message": message,
            "booking_id": booking_id,
            "status": booking.status.value
        }
    
    def check_in(self, booking_id: int, locale: str = "en") -> Dict[str, Any]:
        """
        Отметить заезд гостя.
        
        Args:
            booking_id: ID бронирования
            locale: Язык для сообщений
            
        Returns:
            Dict: Результат операции с сообщением
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
            BookingStatusError: Если бронирование нельзя отметить
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        
        if booking.status != BookingStatus.CONFIRMED:
            raise BookingStatusError(booking_id, booking.status.value, locale)
        
        booking.status = BookingStatus.CHECKED_IN
        
        self.booking_repo.update(booking)
        self.uow.commit()
        
        message = self._get_localized_message(
            "booking.status.checked_in",
            {"booking_id": booking_id},
            locale
        )
        
        return {
            "success": True,
            "message": message,
            "booking_id": booking_id,
            "status": booking.status.value
        }
    
    def check_out(self, booking_id: int, locale: str = "en") -> Dict[str, Any]:
        """
        Отметить выезд гостя.
        
        Args:
            booking_id: ID бронирования
            locale: Язык для сообщений
            
        Returns:
            Dict: Результат операции с сообщением
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
            BookingStatusError: Если бронирование нельзя отметить
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        
        if booking.status != BookingStatus.CHECKED_IN:
            raise BookingStatusError(booking_id, booking.status.value, locale)
        
        booking.status = BookingStatus.CHECKED_OUT
        
        self.booking_repo.update(booking)
        self.uow.commit()
        
        message = self._get_localized_message(
            "booking.status.checked_out",
            {"booking_id": booking_id},
            locale
        )
        
        return {
            "success": True,
            "message": message,
            "booking_id": booking_id,
            "status": booking.status.value
        }
    
    def get_available_rooms(
        self,
        hotel_id: int,
        check_in: date,
        check_out: date,
        capacity: Optional[int] = None,
        locale: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Получить доступные номера с локализованными описаниями.
        
        Args:
            hotel_id: ID отеля
            check_in: Дата заезда
            check_out: Дата выезда
            capacity: Минимальная вместимость (опционально)
            locale: Язык для сообщений
            
        Returns:
            List[Dict]: Список доступных номеров с описанием
            
        Raises:
            HotelNotFoundError: Если отель не найден
        """
        # 1. Проверяем существование отеля
        hotel = self.hotel_repo.get_by_id(hotel_id)
        if not hotel:
            raise HotelNotFoundError(hotel_id, locale)
        
        # 2. Получаем все номера отеля
        rooms = self.room_repo.get_by_hotel(hotel_id, active_only=True)
        
        # 3. Фильтруем по вместимости
        if capacity:
            rooms = [r for r in rooms if r.capacity >= capacity]
        
        # 4. Для каждого номера проверяем доступность
        available = []
        for room in rooms:
            existing = self.booking_repo.get_by_room_and_dates(
                room.id, check_in, check_out
            )
            if not existing:
                status_text = self._get_localized_message(
                    "room.available",
                    {"room_id": room.id},
                    locale
                )
                
                available.append({
                    'room_id': room.id,
                    'number': room.number,
                    'capacity': room.capacity,
                    'price_per_night': room.price_per_night,
                    'room_type': room.room_type,
                    'status_text': status_text
                })
        
        return available
    
    def get_by_id(self, booking_id: int, locale: str = "en") -> BookingResponseDTO:
        """
        Получить бронирование по ID с локализацией.
        
        Args:
            booking_id: ID бронирования
            locale: Язык для сообщений
            
        Returns:
            BookingResponseDTO: Найденное бронирование
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        
        message = self._get_status_message(booking_id, booking.status, locale)
        return BookingResponseDTO.from_booking(booking, locale, message)
    
    def get_by_guest(self, email: str, locale: str = "en") -> List[BookingResponseDTO]:
        """
        Получить все бронирования гостя.
        
        Args:
            email: Email гостя
            locale: Язык для сообщений
            
        Returns:
            List[BookingResponseDTO]: Список бронирований
        """
        bookings = self.booking_repo.get_all(guest_email=email)
        result = []
        for booking in bookings:
            message = self._get_status_message(booking.id, booking.status, locale)
            result.append(BookingResponseDTO.from_booking(booking, locale, message))
        return result
    
    def get_by_room(self, room_id: int, locale: str = "en") -> List[BookingResponseDTO]:
        """
        Получить все бронирования для номера.
        
        Args:
            room_id: ID номера
            locale: Язык для сообщений
            
        Returns:
            List[BookingResponseDTO]: Список бронирований
        """
        bookings = self.booking_repo.get_all(room_id=room_id)
        result = []
        for booking in bookings:
            message = self._get_status_message(booking.id, booking.status, locale)
            result.append(BookingResponseDTO.from_booking(booking, locale, message))
        return result
    
    def get_status_text(self, booking_id: int, locale: str = "en") -> str:
        """
        Получить локализованный текст статуса бронирования.
        
        Args:
            booking_id: ID бронирования
            locale: Язык для сообщений
            
        Returns:
            str: Локализованный статус
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        return self._get_status_message(booking_id, booking.status, locale)
    
    def get_all_pending(self, locale: str = "en") -> List[BookingResponseDTO]:
        """
        Получить все ожидающие бронирования.
        
        Args:
            locale: Язык для сообщений
            
        Returns:
            List[BookingResponseDTO]: Список ожидающих бронирований
        """
        bookings = self.booking_repo.get_pending_bookings()
        result = []
        for booking in bookings:
            message = self._get_status_message(booking.id, booking.status, locale)
            result.append(BookingResponseDTO.from_booking(booking, locale, message))
        return result
    
    def update(self, booking_id: int, dto: BookingUpdateDTO, locale: str = "en") -> BookingResponseDTO:
        """
        Обновить бронирование.
        
        Args:
            booking_id: ID бронирования
            dto: Данные для обновления
            locale: Язык для сообщений
            
        Returns:
            BookingResponseDTO: Обновленное бронирование
            
        Raises:
            BookingNotFoundError: Если бронирование не найдено
            BookingStatusError: Если бронирование нельзя изменить
        """
        booking = self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFoundError(booking_id, locale)
        
        # Нельзя изменять бронирование в некоторых статусах
        if booking.status in (BookingStatus.CHECKED_IN, BookingStatus.CHECKED_OUT, BookingStatus.CANCELLED):
            raise BookingStatusError(booking_id, booking.status.value, locale)
        
        # Обновляем поля
        if dto.guest_name is not None:
            booking.guest_name = dto.guest_name
        if dto.guest_email is not None:
            booking.guest_email = dto.guest_email
        
        # Обновляем даты только если они есть
        if dto.check_in and dto.check_out:
            # Проверяем конфликты с новыми датами
            existing = self.booking_repo.get_by_room_and_dates(
                booking.room_id, dto.check_in, dto.check_out
            )
            # Исключаем текущее бронирование из проверки
            existing = [b for b in existing if b.id != booking_id]
            if existing:
                raise BookingConflictError(
                    booking.room_id,
                    dto.check_in.isoformat(),
                    dto.check_out.isoformat(),
                    locale
                )
            
            # Пересчитываем стоимость
            room = self.room_repo.get_by_id(booking.room_id)
            if room:
                booking.total_price = self.pricing_service.calculate_price(
                    room, dto.check_in, dto.check_out
                )
            
            booking.check_in = dto.check_in
            booking.check_out = dto.check_out
        
        updated = self.booking_repo.update(booking)
        self.uow.commit()
        
        message = self._get_localized_message(
            "booking.created",
            {"booking_id": booking_id},
            locale
        )
        
        return BookingResponseDTO.from_booking(updated, locale, message)