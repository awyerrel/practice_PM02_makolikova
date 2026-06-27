# src/utils/validators.py
"""
Модуль валидации данных для системы логистики и бронирования

Предоставляет:
- Валидацию координат
- Валидацию дат и времени
- Валидацию цен и денежных сумм
- Валидацию рейтингов
- Валидацию типов транспорта
- Валидацию email и телефонов
- Валидацию граничных значений
- Декораторы для автоматической валидации
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional, Union, List, Any, Callable, TypeVar, Generic
from decimal import Decimal, InvalidOperation
from functools import wraps
import math

from src.core.exceptions import ValidationError


# --- Базовые классы валидаторов ---

T = TypeVar('T')


class Validator(Generic[T]):
    """Базовый класс для валидаторов"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "Validation failed"
    
    def validate(self, value: T) -> T:
        """
        Валидировать значение
        
        Args:
            value: Значение для валидации
            
        Returns:
            Валидированное значение
            
        Raises:
            ValidationError: Если валидация не пройдена
        """
        return value
    
    def __call__(self, value: T) -> T:
        return self.validate(value)


class ComposedValidator(Validator[T]):
    """Композитный валидатор, объединяющий несколько валидаторов"""
    
    def __init__(self, validators: List[Validator], message: Optional[str] = None):
        super().__init__(message)
        self.validators = validators
    
    def validate(self, value: T) -> T:
        for validator in self.validators:
            value = validator.validate(value)
        return value


# --- Валидаторы для примитивных типов ---

class NotNullValidator(Validator):
    """Проверка, что значение не None"""
    
    def validate(self, value: Any) -> Any:
        if value is None:
            raise ValidationError(self.message or "Value cannot be None")
        return value


class NotEmptyValidator(Validator):
    """Проверка, что значение не пустое"""
    
    def validate(self, value: Any) -> Any:
        if not value:
            raise ValidationError(self.message or "Value cannot be empty")
        return value


class TypeValidator(Validator):
    """Проверка типа значения"""
    
    def __init__(self, expected_type: type, message: Optional[str] = None):
        super().__init__(message)
        self.expected_type = expected_type
    
    def validate(self, value: Any) -> Any:
        if not isinstance(value, self.expected_type):
            raise ValidationError(
                self.message or f"Expected {self.expected_type.__name__}, got {type(value).__name__}"
            )
        return value


class RangeValidator(Validator):
    """Проверка, что значение входит в диапазон"""
    
    def __init__(
        self,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        message: Optional[str] = None
    ):
        super().__init__(message)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Union[int, float]) -> Union[int, float]:
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                self.message or f"Value {value} is less than minimum {self.min_value}"
            )
        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                self.message or f"Value {value} is greater than maximum {self.max_value}"
            )
        return value


class LengthValidator(Validator):
    """Проверка длины строки или списка"""
    
    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        message: Optional[str] = None
    ):
        super().__init__(message)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Union[str, list]) -> Union[str, list]:
        length = len(value)
        if self.min_length is not None and length < self.min_length:
            raise ValidationError(
                self.message or f"Length {length} is less than minimum {self.min_length}"
            )
        if self.max_length is not None and length > self.max_length:
            raise ValidationError(
                self.message or f"Length {length} is greater than maximum {self.max_length}"
            )
        return value


class PatternValidator(Validator):
    """Проверка соответствия регулярному выражению"""
    
    def __init__(self, pattern: str, message: Optional[str] = None):
        super().__init__(message)
        self.pattern = re.compile(pattern)
    
    def validate(self, value: str) -> str:
        if not self.pattern.match(value):
            raise ValidationError(
                self.message or f"Value '{value}' does not match pattern {self.pattern.pattern}"
            )
        return value


# --- Специализированные валидаторы ---

class CoordinatesValidator:
    """Валидатор координат"""
    
    @staticmethod
    def validate_lat(lat: float) -> float:
        """Валидация широты (-90 до 90)"""
        if not isinstance(lat, (int, float)):
            raise ValidationError(f"Latitude must be number, got {type(lat).__name__}")
        
        if not (-90 <= lat <= 90):
            raise ValidationError(f"Latitude {lat} must be between -90 and 90")
        
        return lat
    
    @staticmethod
    def validate_lon(lon: float) -> float:
        """Валидация долготы (-180 до 180)"""
        if not isinstance(lon, (int, float)):
            raise ValidationError(f"Longitude must be number, got {type(lon).__name__}")
        
        if not (-180 <= lon <= 180):
            raise ValidationError(f"Longitude {lon} must be between -180 and 180")
        
        return lon
    
    @staticmethod
    def validate_coordinates(lat: float, lon: float) -> tuple:
        """Валидация обоих координат"""
        lat = CoordinatesValidator.validate_lat(lat)
        lon = CoordinatesValidator.validate_lon(lon)
        return lat, lon
    
    @staticmethod
    def validate_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        max_distance_km: Optional[float] = None
    ) -> float:
        """
        Валидация расстояния между точками
        
        Args:
            lat1, lon1: Координаты первой точки
            lat2, lon2: Координаты второй точки
            max_distance_km: Максимальное допустимое расстояние
            
        Returns:
            Расстояние в км
            
        Raises:
            ValidationError: Если расстояние превышает максимальное
        """
        # Валидируем координаты
        CoordinatesValidator.validate_coordinates(lat1, lon1)
        CoordinatesValidator.validate_coordinates(lat2, lon2)
        
        # Вычисляем расстояние (приблизительная формула)
        R = 6371  # Радиус Земли в км
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        if max_distance_km is not None and distance > max_distance_km:
            raise ValidationError(
                f"Distance {distance:.2f} km exceeds maximum {max_distance_km} km"
            )
        
        return distance


class DateValidator:
    """Валидатор дат и времени"""
    
    @staticmethod
    def validate_date(date_str: str, format: str = '%Y-%m-%d') -> datetime:
        """Валидация строки даты"""
        try:
            return datetime.strptime(date_str, format)
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_str}. Expected format: {format}")
    
    @staticmethod
    def validate_date_range(
        start_date: Union[datetime, date, str],
        end_date: Union[datetime, date, str],
        min_gap_days: Optional[int] = None,
        max_gap_days: Optional[int] = None
    ) -> tuple:
        """
        Валидация диапазона дат
        
        Args:
            start_date: Дата начала
            end_date: Дата окончания
            min_gap_days: Минимальный разрыв в днях
            max_gap_days: Максимальный разрыв в днях
            
        Returns:
            Кортеж (start_date, end_date) как datetime
            
        Raises:
            ValidationError: Если даты невалидны
        """
        # Преобразуем строки в datetime
        if isinstance(start_date, str):
            start_date = DateValidator.validate_date(start_date)
        if isinstance(end_date, str):
            end_date = DateValidator.validate_date(end_date)
        
        # Проверяем, что даты - datetime
        if not isinstance(start_date, (datetime, date)):
            raise ValidationError(f"Invalid start date type: {type(start_date).__name__}")
        if not isinstance(end_date, (datetime, date)):
            raise ValidationError(f"Invalid end date type: {type(end_date).__name__}")
        
        # Преобразуем date в datetime
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.min.time())
        
        # Проверяем, что start_date <= end_date
        if start_date > end_date:
            raise ValidationError("Start date must be before or equal to end date")
        
        # Проверяем разрыв
        gap_days = (end_date - start_date).days
        if min_gap_days is not None and gap_days < min_gap_days:
            raise ValidationError(
                f"Minimum gap is {min_gap_days} days, got {gap_days} days"
            )
        if max_gap_days is not None and gap_days > max_gap_days:
            raise ValidationError(
                f"Maximum gap is {max_gap_days} days, got {gap_days} days"
            )
        
        return start_date, end_date
    
    @staticmethod
    def validate_not_past(date_value: Union[datetime, date], allow_today: bool = True) -> datetime:
        """Проверка, что дата не в прошлом"""
        if not isinstance(date_value, (datetime, date)):
            raise ValidationError(f"Invalid date type: {type(date_value).__name__}")
        
        now = datetime.now()
        check_date = date_value
        
        if isinstance(check_date, date) and not isinstance(check_date, datetime):
            check_date = datetime.combine(check_date, datetime.min.time())
        
        if allow_today:
            # Проверяем, что дата >= сегодня
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if check_date < today:
                raise ValidationError("Date cannot be in the past")
        else:
            # Проверяем, что дата > сегодня
            if check_date <= datetime.now():
                raise ValidationError("Date must be in the future")
        
        return date_value


class PriceValidator:
    """Валидатор цен и денежных сумм"""
    
    @staticmethod
    def validate_price(price: Union[int, float, Decimal, str]) -> Decimal:
        """Валидация цены"""
        try:
            if isinstance(price, str):
                price = Decimal(price.replace(' ', '').replace(',', '.'))
            elif not isinstance(price, Decimal):
                price = Decimal(str(price))
        except InvalidOperation:
            raise ValidationError(f"Invalid price format: {price}")
        
        if price < 0:
            raise ValidationError(f"Price cannot be negative: {price}")
        
        # Проверяем точность (не более 2 знаков после запятой)
        if price.as_tuple().exponent < -2:
            raise ValidationError(f"Price cannot have more than 2 decimal places: {price}")
        
        return price
    
    @staticmethod
    def validate_discount(discount: Union[int, float, Decimal]) -> Decimal:
        """Валидация скидки (0-100%)"""
        discount = PriceValidator.validate_price(discount)
        
        if discount < 0 or discount > 100:
            raise ValidationError(f"Discount must be between 0 and 100, got {discount}")
        
        return discount


class RatingValidator:
    """Валидатор рейтинга"""
    
    @staticmethod
    def validate_rating(rating: float) -> float:
        """Валидация рейтинга (1-5)"""
        if not isinstance(rating, (int, float)):
            raise ValidationError(f"Rating must be number, got {type(rating).__name__}")
        
        if rating < 0 or rating > 5:
            raise ValidationError(f"Rating must be between 0 and 5, got {rating}")
        
        # Округляем до 1 знака
        rating = round(rating, 1)
        
        return rating
    
    @staticmethod
    def validate_rating_stars(rating: float) -> int:
        """Валидация рейтинга в звездах (1-5)"""
        rating = RatingValidator.validate_rating(rating)
        return int(round(rating))


class TransportTypeValidator:
    """Валидатор типа транспорта"""
    
    VALID_TYPES = {'car', 'bus', 'train', 'plane', 'walk', 'bicycle', 'ship'}
    
    @staticmethod
    def validate(transport_type: str) -> str:
        """Валидация типа транспорта"""
        transport_type = transport_type.lower().strip()
        
        if transport_type not in TransportTypeValidator.VALID_TYPES:
            raise ValidationError(
                f"Invalid transport type: {transport_type}. "
                f"Valid types: {', '.join(sorted(TransportTypeValidator.VALID_TYPES))}"
            )
        
        return transport_type
    
    @staticmethod
    def get_speed(transport_type: str) -> float:
        """Получить среднюю скорость для типа транспорта (км/ч)"""
        transport_type = TransportTypeValidator.validate(transport_type)
        
        speeds = {
            'car': 60.0,
            'bus': 40.0,
            'train': 80.0,
            'plane': 800.0,
            'walk': 5.0,
            'bicycle': 15.0,
            'ship': 30.0
        }
        
        return speeds.get(transport_type, 50.0)


class EmailValidator:
    """Валидатор email адресов"""
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Валидация email"""
        if not email:
            raise ValidationError("Email cannot be empty")
        
        email = email.strip().lower()
        
        if not EmailValidator.EMAIL_PATTERN.match(email):
            raise ValidationError(f"Invalid email format: {email}")
        
        # Проверяем длину
        if len(email) > 254:
            raise ValidationError(f"Email is too long: {len(email)} characters")
        
        local_part, domain = email.split('@')
        
        if len(local_part) > 64:
            raise ValidationError(f"Local part is too long: {len(local_part)} characters")
        
        return email


class PhoneValidator:
    """Валидатор телефонных номеров"""
    
    PHONE_PATTERN = re.compile(
        r'^(\+7|8)?\s*\(?\d{3}\)?\s*\d{3}\s*-?\s*\d{2}\s*-?\s*\d{2}$'
    )
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Валидация телефона"""
        if not phone:
            raise ValidationError("Phone cannot be empty")
        
        phone = phone.strip()
        
        # Удаляем пробелы и дефисы
        cleaned = re.sub(r'[\s\-()]', '', phone)
        
        # Проверяем формат
        if not PhoneValidator.PHONE_PATTERN.match(phone):
            raise ValidationError(f"Invalid phone format: {phone}")
        
        return phone


class PasswordValidator:
    """Валидатор паролей"""
    
    @staticmethod
    def validate_password(password: str, min_length: int = 8) -> str:
        """Валидация пароля"""
        if not password:
            raise ValidationError("Password cannot be empty")
        
        if len(password) < min_length:
            raise ValidationError(
                f"Password must be at least {min_length} characters long"
            )
        
        # Проверяем наличие разных типов символов
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not has_upper:
            raise ValidationError("Password must contain at least one uppercase letter")
        if not has_lower:
            raise ValidationError("Password must contain at least one lowercase letter")
        if not has_digit:
            raise ValidationError("Password must contain at least one digit")
        if not has_special:
            raise ValidationError("Password must contain at least one special character")
        
        return password


# --- Декораторы для валидации ---

def validate_input(*validators: Validator):
    """
    Декоратор для валидации входных параметров функции
    
    Example:
        @validate_input(
            NotNullValidator(),
            TypeValidator(str),
            LengthValidator(min_length=1)
        )
        def process_name(name: str):
            return name.upper()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Валидируем аргументы
            new_args = []
            for i, (arg, validator) in enumerate(zip(args, validators)):
                try:
                    validated = validator.validate(arg)
                    new_args.append(validated)
                except ValidationError as e:
                    param_name = func.__code__.co_varnames[i] if i < len(func.__code__.co_varnames) else f"arg_{i}"
                    raise ValidationError(f"Parameter '{param_name}': {str(e)}")
            
            # Добавляем оставшиеся аргументы без валидации
            new_args.extend(args[len(validators):])
            
            return func(*new_args, **kwargs)
        return wrapper
    return decorator


def validate_result(validator: Validator):
    """
    Декоратор для валидации результата функции
    
    Example:
        @validate_result(RangeValidator(min_value=0))
        def calculate_total(price: float, quantity: int) -> float:
            return price * quantity
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return validator.validate(result)
        return wrapper
    return decorator


# --- Фабрика валидаторов ---

class ValidatorFactory:
    """Фабрика для создания валидаторов"""
    
    @staticmethod
    def for_coordinates():
        """Создать валидатор для координат"""
        return ComposedValidator([
            NotNullValidator("Coordinates cannot be null")
        ])
    
    @staticmethod
    def for_price():
        """Создать валидатор для цены"""
        return ComposedValidator([
            NotNullValidator("Price cannot be null"),
            RangeValidator(min_value=0, message="Price cannot be negative")
        ])
    
    @staticmethod
    def for_rating():
        """Создать валидатор для рейтинга"""
        return ComposedValidator([
            NotNullValidator("Rating cannot be null"),
            RangeValidator(min_value=1, max_value=5, message="Rating must be between 1 and 5")
        ])
    
    @staticmethod
    def for_date():
        """Создать валидатор для даты"""
        return ComposedValidator([
            NotNullValidator("Date cannot be null"),
        ])
    
    @staticmethod
    def for_string(min_length: int = 0, max_length: Optional[int] = None):
        """Создать валидатор для строки"""
        return ComposedValidator([
            NotNullValidator("String cannot be null"),
            LengthValidator(min_length=min_length, max_length=max_length)
        ])
    
    @staticmethod
    def for_email():
        """Создать валидатор для email"""
        class EmailValidatorWrapper(Validator):
            def validate(self, value):
                return EmailValidator.validate_email(value)
        
        return EmailValidatorWrapper()
    
    @staticmethod
    def for_phone():
        """Создать валидатор для телефона"""
        class PhoneValidatorWrapper(Validator):
            def validate(self, value):
                return PhoneValidator.validate_phone(value)
        
        return PhoneValidatorWrapper()


# --- Вспомогательные функции ---

def validate_route_segments(segments: list) -> bool:
    """Валидация сегментов маршрута"""
    if not segments:
        raise ValidationError("Route must have at least one segment")
    
    for i, segment in enumerate(segments):
        if not segment.start:
            raise ValidationError(f"Segment {i+1}: start location is required")
        if not segment.end:
            raise ValidationError(f"Segment {i+1}: end location is required")
        if segment.start == segment.end:
            raise ValidationError(f"Segment {i+1}: start and end locations must be different")
        
        # Проверяем транспорт
        TransportTypeValidator.validate(segment.transport_type.value)
    
    return True


def validate_booking_dates(check_in: datetime, check_out: datetime) -> bool:
    """Валидация дат бронирования"""
    # Проверяем, что даты не в прошлом
    check_in = DateValidator.validate_not_past(check_in)
    check_out = DateValidator.validate_not_past(check_out)
    
    # Проверяем диапазон
    DateValidator.validate_date_range(check_in, check_out, min_gap_days=1)
    
    return True


def validate_hotel_amenities(amenities: list) -> bool:
    """Валидация удобств отеля"""
    if not amenities:
        return True
    
    if len(amenities) > 20:
        raise ValidationError("Too many amenities (max 20)")
    
    for amenity in amenities:
        if len(amenity) > 50:
            raise ValidationError(f"Amenity too long: {amenity[:50]}...")
        
        if not amenity.strip():
            raise ValidationError("Amenity cannot be empty")
    
    return True


# --- Пример использования ---

def example_usage():
    """Пример использования валидаторов"""
    
    print("="*50)
    print("Пример использования валидаторов")
    print("="*50)
    
    # 1. Валидация координат
    print("\n1. Валидация координат:")
    try:
        lat, lon = CoordinatesValidator.validate_coordinates(55.7558, 37.6173)
        print(f"  ✅ Корректные координаты: {lat}, {lon}")
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    try:
        CoordinatesValidator.validate_coordinates(100, 200)
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    # 2. Валидация дат
    print("\n2. Валидация дат:")
    try:
        start = DateValidator.validate_date('2026-07-01')
        end = DateValidator.validate_date('2026-07-07')
        start, end = DateValidator.validate_date_range(start, end, min_gap_days=1)
        print(f"  ✅ Диапазон дат: {start.date()} - {end.date()}")
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    # 3. Валидация цены
    print("\n3. Валидация цены:")
    try:
        price = PriceValidator.validate_price("1500.50")
        print(f"  ✅ Цена: {price}")
        
        PriceValidator.validate_price(-100)
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    # 4. Валидация рейтинга
    print("\n4. Валидация рейтинга:")
    try:
        rating = RatingValidator.validate_rating(4.5)
        print(f"  ✅ Рейтинг: {rating}")
        
        RatingValidator.validate_rating(5.5)
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    # 5. Валидация email
    print("\n5. Валидация email:")
    try:
        email = EmailValidator.validate_email("test@example.com")
        print(f"  ✅ Email: {email}")
        
        EmailValidator.validate_email("invalid-email")
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    # 6. Использование декоратора
    print("\n6. Использование декоратора @validate_input:")
    
    @validate_input(
        NotNullValidator("Name cannot be null"),
        TypeValidator(str, "Name must be string"),
        LengthValidator(min_length=2, max_length=50, message="Name length must be 2-50")
    )
    def process_name(name: str) -> str:
        return name.upper()
    
    try:
        result = process_name("John")
        print(f"  ✅ Результат: {result}")
        
        process_name("")
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    # 7. Использование фабрики
    print("\n7. Использование ValidatorFactory:")
    
    email_validator = ValidatorFactory.for_email()
    try:
        email = email_validator.validate("user@domain.com")
        print(f"  ✅ Email: {email}")
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    price_validator = ValidatorFactory.for_price()
    try:
        price = price_validator.validate(100.50)
        print(f"  ✅ Цена: {price}")
    except ValidationError as e:
        print(f"  ❌ {e}")
    
    print("\n" + "="*50)
    print("Пример завершен")
    print("="*50)


if __name__ == "__main__":
    example_usage()