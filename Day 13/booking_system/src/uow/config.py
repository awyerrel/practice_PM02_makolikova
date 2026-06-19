from typing import Dict, List, Any
import os


class Config:
    """
    Конфигурация приложения.
    Содержит все настройки для системы управления бронированиями.
    """
    
    # ЛОКАЛИЗАЦИЯ
    # Поддерживаемые языки (Internationalization)
    SUPPORTED_LOCALES: List[str] = ["en", "ru"]
    DEFAULT_LOCALE: str = "en"
    
    # БИЗНЕС-ПРАВИЛА
    # Минимальный рейтинг отеля для бронирования
    MIN_HOTEL_RATING: float = 3.0
    
    # Максимальная длительность бронирования (дней)
    MAX_BOOKING_DAYS: int = 30
    
    # Минимальная длительность бронирования (дней)
    MIN_BOOKING_DAYS: int = 1
    
    # СЕЗОННЫЕ КОЭФФИЦИЕНТЫ
    # Коэффициенты для разных месяцев (1 = январь, 12 = декабрь)
    SEASONAL_COEFFICIENTS: Dict[int, float] = {
        1: 1.1,   # январь - новогодние праздники
        2: 1.0,   # февраль
        3: 1.0,   # март
        4: 1.0,   # апрель
        5: 1.1,   # май - праздники
        6: 1.2,   # июнь - начало лета
        7: 1.5,   # июль - пик сезона
        8: 1.5,   # август - пик сезона
        9: 1.2,   # сентябрь - бархатный сезон
        10: 1.1,  # октябрь
        11: 1.0,  # ноябрь
        12: 1.3,  # декабрь - новый год
    }
    
    # СКИДКИ
    # Скидки за длительное бронирование
    LONG_STAY_DISCOUNT_DAYS: int = 7
    LONG_STAY_DISCOUNT_PERCENT: float = 5.0  # 5%
    
    EXTRA_LONG_STAY_DISCOUNT_DAYS: int = 14
    EXTRA_LONG_STAY_DISCOUNT_PERCENT: float = 10.0  # 10%
    
    # ВАЛИДАЦИЯ
    # Максимальный рейтинг отеля
    MAX_HOTEL_RATING: float = 5.0
    
    # Минимальный рейтинг отеля
    MIN_HOTEL_RATING_VALUE: float = 0.0
    
    # ТИПЫ НОМЕРОВ
    ALLOWED_ROOM_TYPES: List[str] = ["standard", "deluxe", "suite"]
    
    # СТАТУСЫ БРОНИРОВАНИЙ
    ALLOWED_BOOKING_STATUSES: List[str] = [
        "pending",
        "confirmed",
        "checked_in",
        "checked_out",
        "cancelled"
    ]
    
    # ПУТИ
    # Базовая директория проекта
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    
    # НАСТРОЙКИ ТЕСТИРОВАНИЯ
    # Режим тестирования
    TESTING: bool = False
    
    # Использовать In-Memory репозитории (для тестов)
    USE_IN_MEMORY_REPOSITORIES: bool = True
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        Получить всю конфигурацию в виде словаря.
        
        Returns:
            Dict[str, Any]: Словарь со всеми настройками
        """
        return {
            "supported_locales": cls.SUPPORTED_LOCALES,
            "default_locale": cls.DEFAULT_LOCALE,
            "min_hotel_rating": cls.MIN_HOTEL_RATING,
            "max_booking_days": cls.MAX_BOOKING_DAYS,
            "min_booking_days": cls.MIN_BOOKING_DAYS,
            "seasonal_coefficients": cls.SEASONAL_COEFFICIENTS,
            "allowed_room_types": cls.ALLOWED_ROOM_TYPES,
            "allowed_booking_statuses": cls.ALLOWED_BOOKING_STATUSES,
            "testing": cls.TESTING,
            "use_in_memory_repositories": cls.USE_IN_MEMORY_REPOSITORIES,
        }
    
    @classmethod
    def get_seasonal_coefficient(cls, month: int) -> float:
        """
        Получить сезонный коэффициент для месяца.
        
        Args:
            month: Номер месяца (1-12)
            
        Returns:
            float: Коэффициент
        """
        return cls.SEASONAL_COEFFICIENTS.get(month, 1.0)
    
    @classmethod
    def set_testing_mode(cls, enabled: bool = True) -> None:
        """
        Установить режим тестирования.
        
        Args:
            enabled: Включить/выключить режим тестирования
        """
        cls.TESTING = enabled
    
    @classmethod
    def is_valid_locale(cls, locale: str) -> bool:
        """
        Проверить, поддерживается ли локаль.
        
        Args:
            locale: Код локали (en, ru)
            
        Returns:
            bool: True если поддерживается
        """
        return locale in cls.SUPPORTED_LOCALES
    
    @classmethod
    def is_valid_room_type(cls, room_type: str) -> bool:
        """
        Проверить, является ли тип номера допустимым.
        
        Args:
            room_type: Тип номера
            
        Returns:
            bool: True если допустим
        """
        return room_type in cls.ALLOWED_ROOM_TYPES
    
    @classmethod
    def is_valid_booking_status(cls, status: str) -> bool:
        """
        Проверить, является ли статус бронирования допустимым.
        
        Args:
            status: Статус бронирования
            
        Returns:
            bool: True если допустим
        """
        return status in cls.ALLOWED_BOOKING_STATUSES
    
    @classmethod
    def get_long_stay_discount(cls, nights: int) -> float:
        """
        Получить скидку за длительное бронирование.
        
        Args:
            nights: Количество ночей
            
        Returns:
            float: Процент скидки
        """
        if nights >= cls.EXTRA_LONG_STAY_DISCOUNT_DAYS:
            return cls.EXTRA_LONG_STAY_DISCOUNT_PERCENT
        elif nights >= cls.LONG_STAY_DISCOUNT_DAYS:
            return cls.LONG_STAY_DISCOUNT_PERCENT
        return 0.0


# Создаем экземпляр конфигурации для удобного импорта
config = Config()


# ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
# Настройки для разных окружений

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    TESTING: bool = False
    USE_IN_MEMORY_REPOSITORIES: bool = True


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING: bool = True
    USE_IN_MEMORY_REPOSITORIES: bool = True
    MIN_HOTEL_RATING: float = 0.0  # Для тестов снимаем ограничение


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    TESTING: bool = False
    USE_IN_MEMORY_REPOSITORIES: bool = False  # В продакшене использовать реальную БД


# ФАБРИКА КОНФИГУРАЦИИ
class ConfigFactory:
    """
    Фабрика для создания конфигурации в зависимости от окружения.
    """
    
    @staticmethod
    def get_config(environment: str = "development") -> Config:
        """
        Получить конфигурацию для указанного окружения.
        
        Args:
            environment: Окружение (development, testing, production)
            
        Returns:
            Config: Конфигурация
        """
        environments = {
            "development": DevelopmentConfig,
            "testing": TestingConfig,
            "production": ProductionConfig,
        }
        
        config_class = environments.get(environment, DevelopmentConfig)
        return config_class()