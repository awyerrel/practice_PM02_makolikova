from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional


class BookingCreateDTO(BaseModel):
    """DTO для создания бронирования"""
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    locale: str = "en"  
    
    @field_validator('check_out')
    def validate_dates(cls, v, info):
        """Валидация дат: выезд должен быть позже заезда, не более 30 дней"""
        values = info.data
        if 'check_in' in values:
            if v <= values['check_in']:
                raise ValueError("check_out_must_be_after_check_in")
            if (v - values['check_in']).days > 30:
                raise ValueError("booking_exceeds_max_duration")
        return v
    
    @field_validator('guest_email')
    def validate_email(cls, v):
        """Валидация email: должен содержать @ и ."""
        if '@' not in v or '.' not in v:
            raise ValueError("invalid_email_format")
        return v
    
    @field_validator('locale')
    def validate_locale(cls, v):
        """Валидация локали: только en или ru"""
        if v not in ["en", "ru"]:
            return "en"
        return v


class BookingResponseDTO(BaseModel):
    """DTO для ответа с данными бронирования"""
    id: int
    room_id: int
    guest_name: str
    guest_email: str
    check_in: date
    check_out: date
    total_price: float
    status: str
    created_at: datetime
    locale: str = "en"
    message: Optional[str] = None  
    
    @classmethod
    def from_booking(cls, booking, locale: str = "en", message: str = None):
        """Создать DTO из модели Booking"""
        return cls(
            id=booking.id,
            room_id=booking.room_id,
            guest_name=booking.guest_name,
            guest_email=booking.guest_email,
            check_in=booking.check_in,
            check_out=booking.check_out,
            total_price=booking.total_price,
            status=booking.status.value,
            created_at=booking.created_at,
            locale=locale or booking.locale,
            message=message
        )


class BookingUpdateDTO(BaseModel):
    """DTO для обновления бронирования"""
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    
    @field_validator('check_out')
    def validate_dates(cls, v, info):
        """Валидация дат при обновлении"""
        values = info.data
        if 'check_in' in values and values['check_in'] is not None:
            if v <= values['check_in']:
                raise ValueError("check_out_must_be_after_check_in")
        return v
    
    @field_validator('guest_email')
    def validate_email(cls, v):
        """Валидация email при обновлении"""
        if v is not None:
            if '@' not in v or '.' not in v:
                raise ValueError("invalid_email_format")
        return v