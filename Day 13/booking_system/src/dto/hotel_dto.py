from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class HotelCreateDTO(BaseModel):
    """DTO для создания отеля"""
    name: str
    address: str
    phone: str
    rating: float = 0.0
    
    @field_validator('rating')
    def validate_rating(cls, v):
        """Валидация рейтинга: от 0 до 5"""
        if v < 0 or v > 5:
            raise ValueError("rating must be between 0 and 5")
        return v
    
    @field_validator('name')
    def validate_name(cls, v):
        """Валидация названия: не пустое"""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()
    
    @field_validator('phone')
    def validate_phone(cls, v):
        """Валидация телефона: не пустой"""
        if not v or not v.strip():
            raise ValueError("phone cannot be empty")
        return v.strip()


class HotelResponseDTO(BaseModel):
    """DTO для ответа с данными отеля"""
    id: int
    name: str
    address: str
    phone: str
    rating: float
    created_at: datetime
    
    @classmethod
    def from_hotel(cls, hotel):
        """Создать DTO из модели Hotel"""
        return cls(
            id=hotel.id,
            name=hotel.name,
            address=hotel.address,
            phone=hotel.phone,
            rating=hotel.rating,
            created_at=hotel.created_at
        )


class HotelUpdateDTO(BaseModel):
    """DTO для обновления отеля"""
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    
    @field_validator('rating')
    def validate_rating(cls, v):
        """Валидация рейтинга при обновлении"""
        if v is not None and (v < 0 or v > 5):
            raise ValueError("rating must be between 0 and 5")
        return v
    
    @field_validator('name')
    def validate_name(cls, v):
        """Валидация названия при обновлении"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("name cannot be empty")
        return v.strip() if v else v
    
    @field_validator('phone')
    def validate_phone(cls, v):
        """Валидация телефона при обновлении"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("phone cannot be empty")
        return v.strip() if v else v


class HotelSearchDTO(BaseModel):
    """DTO для поиска отелей"""
    name: Optional[str] = None
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    
    @field_validator('min_rating', 'max_rating')
    def validate_rating_range(cls, v):
        """Валидация диапазона рейтинга"""
        if v is not None and (v < 0 or v > 5):
            raise ValueError("rating must be between 0 and 5")
        return v