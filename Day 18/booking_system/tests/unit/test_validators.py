# tests/unit/test_validators.py
"""
Тесты для валидаторов
"""
import pytest
from src.core.exceptions import ValidationError
from src.utils.validators import (
    CoordinatesValidator, DateValidator, 
    PriceValidator, RatingValidator,
    EmailValidator, PhoneValidator,
    TransportTypeValidator
)


class TestValidators:
    """Тесты для валидаторов"""
    
    def test_validate_coordinates_valid(self):
        """Валидация корректных координат"""
        # Должна пройти без исключений
        lat, lon = CoordinatesValidator.validate_coordinates(55.7558, 37.6173)
        assert lat == 55.7558
        assert lon == 37.6173
    
    def test_validate_coordinates_invalid_lat(self):
        """Валидация невалидной широты"""
        with pytest.raises(ValidationError):
            CoordinatesValidator.validate_coordinates(100, 37.6173)
        
        with pytest.raises(ValidationError):
            CoordinatesValidator.validate_coordinates(-100, 37.6173)
    
    def test_validate_coordinates_invalid_lon(self):
        """Валидация невалидной долготы"""
        with pytest.raises(ValidationError):
            CoordinatesValidator.validate_coordinates(55.7558, 200)
        
        with pytest.raises(ValidationError):
            CoordinatesValidator.validate_coordinates(55.7558, -200)
    
    def test_validate_date_valid(self):
        """Валидация корректной даты"""
        date = DateValidator.validate_date('2026-07-01')
        assert date is not None
    
    def test_validate_date_invalid(self):
        """Валидация невалидной даты"""
        with pytest.raises(ValidationError):
            DateValidator.validate_date('2026-13-01')
    
    def test_validate_price_valid(self):
        """Валидация корректной цены"""
        price = PriceValidator.validate_price(100.50)
        assert price == 100.50
    
    def test_validate_price_negative(self):
        """Валидация отрицательной цены"""
        with pytest.raises(ValidationError):
            PriceValidator.validate_price(-100)
    
    def test_validate_rating_valid(self):
        """Валидация корректного рейтинга"""
        rating = RatingValidator.validate_rating(4.5)
        assert rating == 4.5
    
    def test_validate_rating_invalid(self):
        """Валидация невалидного рейтинга"""
        with pytest.raises(ValidationError):
            RatingValidator.validate_rating(5.5)
    
    def test_validate_email_valid(self):
        """Валидация корректного email"""
        email = EmailValidator.validate_email("test@example.com")
        assert email == "test@example.com"
    
    def test_validate_email_invalid(self):
        """Валидация невалидного email"""
        with pytest.raises(ValidationError):
            EmailValidator.validate_email("invalid-email")
    
    def test_validate_phone_valid(self):
        """Валидация корректного телефона"""
        phone = PhoneValidator.validate_phone("+7 999 123-45-67")
        assert phone is not None
    
    def test_validate_phone_invalid(self):
        """Валидация невалидного телефона"""
        with pytest.raises(ValidationError):
            PhoneValidator.validate_phone("123")
    
    def test_validate_transport_type_valid(self):
        """Валидация корректного типа транспорта"""
        transport = TransportTypeValidator.validate("car")
        assert transport == "car"
    
    def test_validate_transport_type_invalid(self):
        """Валидация невалидного типа транспорта"""
        with pytest.raises(ValidationError):
            TransportTypeValidator.validate("helicopter")