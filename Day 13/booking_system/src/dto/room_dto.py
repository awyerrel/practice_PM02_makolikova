from pydantic import BaseModel, field_validator
from datetime import date  # ДОБАВЛЯЕМ ЭТУ СТРОКУ
from typing import Optional


class RoomCreateDTO(BaseModel):
    """DTO для создания номера"""
    hotel_id: int
    number: str
    capacity: int
    price_per_night: float
    room_type: str = "standard"
    is_active: bool = True
    
    @field_validator('capacity')
    def validate_capacity(cls, v):
        if v < 1:
            raise ValueError("capacity must be at least 1")
        return v
    
    @field_validator('price_per_night')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("price_per_night must be greater than 0")
        return v
    
    @field_validator('room_type')
    def validate_room_type(cls, v):
        allowed_types = ["standard", "deluxe", "suite"]
        if v not in allowed_types:
            return "standard"
        return v
    
    @field_validator('number')
    def validate_number(cls, v):
        if not v or not v.strip():
            raise ValueError("number cannot be empty")
        return v.strip()
    
    @field_validator('hotel_id')
    def validate_hotel_id(cls, v):
        if v <= 0:
            raise ValueError("hotel_id must be greater than 0")
        return v


class RoomResponseDTO(BaseModel):
    """DTO для ответа с данными номера"""
    id: int
    hotel_id: int
    number: str
    capacity: int
    price_per_night: float
    is_active: bool
    room_type: str
    
    @classmethod
    def from_room(cls, room):
        return cls(
            id=room.id,
            hotel_id=room.hotel_id,
            number=room.number,
            capacity=room.capacity,
            price_per_night=room.price_per_night,
            is_active=room.is_active,
            room_type=room.room_type
        )


class RoomUpdateDTO(BaseModel):
    """DTO для обновления номера"""
    number: Optional[str] = None
    capacity: Optional[int] = None
    price_per_night: Optional[float] = None
    room_type: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('capacity')
    def validate_capacity(cls, v):
        if v is not None and v < 1:
            raise ValueError("capacity must be at least 1")
        return v
    
    @field_validator('price_per_night')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("price_per_night must be greater than 0")
        return v
    
    @field_validator('room_type')
    def validate_room_type(cls, v):
        if v is not None:
            allowed_types = ["standard", "deluxe", "suite"]
            if v not in allowed_types:
                return "standard"
        return v
    
    @field_validator('number')
    def validate_number(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("number cannot be empty")
        return v.strip() if v else v


class RoomSearchDTO(BaseModel):
    """DTO для поиска номеров"""
    hotel_id: Optional[int] = None
    min_capacity: Optional[int] = None
    max_price: Optional[float] = None
    room_type: Optional[str] = None
    is_active: Optional[bool] = True
    
    @field_validator('min_capacity')
    def validate_capacity(cls, v):
        if v is not None and v < 1:
            raise ValueError("min_capacity must be at least 1")
        return v
    
    @field_validator('max_price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError("max_price must be greater than 0")
        return v
    
    @field_validator('hotel_id')
    def validate_hotel_id(cls, v):
        if v is not None and v <= 0:
            raise ValueError("hotel_id must be greater than 0")
        return v
    
    @field_validator('room_type')
    def validate_room_type(cls, v):
        if v is not None:
            allowed_types = ["standard", "deluxe", "suite"]
            if v not in allowed_types:
                return None
        return v


class RoomAvailabilityDTO(BaseModel):
    """DTO для проверки доступности номера"""
    room_id: int
    check_in: date
    check_out: date
    
    @field_validator('check_out')
    def validate_dates(cls, v, info):
        values = info.data
        if 'check_in' in values and v <= values['check_in']:
            raise ValueError("check_out must be after check_in")
        return v
    
    @field_validator('room_id')
    def validate_room_id(cls, v):
        if v <= 0:
            raise ValueError("room_id must be greater than 0")
        return v