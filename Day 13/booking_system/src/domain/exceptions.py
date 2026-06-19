from typing import Optional, Dict, Any


class DomainError(Exception):
    """Базовое исключение домена"""
    def __init__(self, message: str, details: dict = None, locale: str = "en"):
        self.message = message
        self.details = details or {}
        self.locale = locale
        super().__init__(message)


class RoomNotFoundError(DomainError):
    """Исключение: номер не найден"""
    def __init__(self, room_id: int, locale: str = "en"):
        messages = {
            "en": f"Room with ID {room_id} was not found",
            "ru": f"Номер с ID {room_id} не найден"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"room_id": room_id},
            locale
        )


class RoomNotAvailableError(DomainError):
    """Исключение: номер недоступен"""
    def __init__(self, room_id: int, check_in: str, check_out: str, locale: str = "en"):
        messages = {
            "en": f"Room {room_id} is not available from {check_in} to {check_out}",
            "ru": f"Номер {room_id} недоступен с {check_in} по {check_out}"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"room_id": room_id, "check_in": check_in, "check_out": check_out},
            locale
        )


class BookingNotFoundError(DomainError):
    """Исключение: бронирование не найдено"""
    def __init__(self, booking_id: int, locale: str = "en"):
        messages = {
            "en": f"Booking with ID {booking_id} was not found",
            "ru": f"Бронирование с ID {booking_id} не найдено"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"booking_id": booking_id},
            locale
        )


class BookingConflictError(DomainError):
    """Исключение: конфликт бронирований"""
    def __init__(self, room_id: int, check_in: str, check_out: str, locale: str = "en"):
        messages = {
            "en": f"Room {room_id} is already booked for dates {check_in} - {check_out}",
            "ru": f"Номер {room_id} уже забронирован на даты {check_in} - {check_out}"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"room_id": room_id, "check_in": check_in, "check_out": check_out},
            locale
        )


class InvalidDatesError(DomainError):
    """Исключение: неверные даты"""
    def __init__(self, reason: str, locale: str = "en"):
        messages = {
            "en": f"Invalid dates: {reason}",
            "ru": f"Неверные даты: {reason}"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"reason": reason},
            locale
        )


class HotelNotFoundError(DomainError):
    """Исключение: отель не найден"""
    def __init__(self, hotel_id: int, locale: str = "en"):
        messages = {
            "en": f"Hotel with ID {hotel_id} was not found",
            "ru": f"Отель с ID {hotel_id} не найден"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"hotel_id": hotel_id},
            locale
        )


class HotelRatingTooLowError(DomainError):
    """Исключение: рейтинг отеля слишком низкий"""
    def __init__(self, hotel_id: int, rating: float, min_rating: float, locale: str = "en"):
        messages = {
            "en": f"Hotel with ID {hotel_id} has rating {rating}, which is below minimum required {min_rating}",
            "ru": f"Рейтинг отеля {hotel_id} составляет {rating}, что ниже минимального {min_rating}"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"hotel_id": hotel_id, "rating": rating, "min_rating": min_rating},
            locale
        )


class BookingStatusError(DomainError):
    """Исключение: неверный статус бронирования"""
    def __init__(self, booking_id: int, current_status: str, locale: str = "en"):
        messages = {
            "en": f"Booking {booking_id} cannot be modified in status '{current_status}'",
            "ru": f"Бронирование {booking_id} нельзя изменить в статусе '{current_status}'"
        }
        super().__init__(
            messages.get(locale, messages["en"]),
            {"booking_id": booking_id, "status": current_status},
            locale
        )


class LocaleNotSupportedError(DomainError):
    """Исключение: неподдерживаемая локаль"""
    def __init__(self, locale: str, supported: list, lang: str = "en"):
        messages = {
            "en": f"Locale '{locale}' is not supported. Supported: {', '.join(supported)}",
            "ru": f"Локаль '{locale}' не поддерживается. Поддерживаемые: {', '.join(supported)}"
        }
        super().__init__(
            messages.get(lang, messages["en"]),
            {"locale": locale, "supported": supported},
            lang
        )