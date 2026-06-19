from datetime import date, timedelta
from typing import Optional, Dict
from src.domain.models import Room
from src.domain.exceptions import InvalidDatesError


class PricingService:
    """
    Сервис расчета стоимости с использованием стратегий.
    Поддерживает сезонные коэффициенты и скидки за длительное бронирование.
    """
    
    def __init__(self, seasonal_coefficients: Optional[Dict[int, float]] = None):
        """
        Инициализация сервиса.
        
        Args:
            seasonal_coefficients: Словарь с коэффициентами по месяцам
        """
        self.seasonal_coefficients = seasonal_coefficients or {
            1: 1.1,   # январь
            2: 1.0,   # февраль
            3: 1.0,   # март
            4: 1.0,   # апрель
            5: 1.1,   # май
            6: 1.2,   # июнь
            7: 1.5,   # июль
            8: 1.5,   # август
            9: 1.2,   # сентябрь
            10: 1.1,  # октябрь
            11: 1.0,  # ноябрь
            12: 1.3,  # декабрь (новый год)
        }
    
    def calculate_price(
        self, 
        room: Room, 
        check_in: date, 
        check_out: date
    ) -> float:
        """
        Рассчитать стоимость бронирования.
        
        Args:
            room: Номер
            check_in: Дата заезда
            check_out: Дата выезда
            
        Returns:
            float: Итоговая стоимость
            
        Raises:
            InvalidDatesError: Если даты неверные
        """
        nights = (check_out - check_in).days
        if nights <= 0:
            raise InvalidDatesError(
                "Количество ночей должно быть больше 0",
                "en"
            )
        
        # Рассчитываем стоимость с учетом сезонности
        total = 0.0
        current_date = check_in
        
        for _ in range(nights):
            month = current_date.month
            coefficient = self.seasonal_coefficients.get(month, 1.0)
            total += room.price_per_night * coefficient
            current_date += timedelta(days=1)
        
        # Применяем скидки за длительное бронирование
        if nights >= 7:
            total *= 0.95  # 5% скидка
        if nights >= 14:
            total *= 0.9   # дополнительная скидка (всего 14.5%)
        
        return round(total, 2)
    
    def calculate_price_with_discount(
        self,
        room: Room,
        check_in: date,
        check_out: date,
        discount_percent: float
    ) -> float:
        """
        Рассчитать стоимость с дополнительной скидкой.
        
        Args:
            room: Номер
            check_in: Дата заезда
            check_out: Дата выезда
            discount_percent: Процент скидки (0-100)
            
        Returns:
            float: Итоговая стоимость со скидкой
        """
        base_price = self.calculate_price(room, check_in, check_out)
        discount_factor = 1 - (discount_percent / 100)
        return round(base_price * discount_factor, 2)
    
    def get_seasonal_coefficient(self, month: int) -> float:
        """
        Получить сезонный коэффициент для месяца.
        
        Args:
            month: Номер месяца (1-12)
            
        Returns:
            float: Коэффициент
        """
        return self.seasonal_coefficients.get(month, 1.0)
    
    def add_seasonal_coefficient(self, month: int, coefficient: float) -> None:
        """
        Добавить или обновить сезонный коэффициент.
        
        Args:
            month: Номер месяца (1-12)
            coefficient: Коэффициент
        """
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        if coefficient <= 0:
            raise ValueError("Coefficient must be greater than 0")
        
        self.seasonal_coefficients[month] = coefficient
    
    def get_price_per_night(self, room: Room, date: date) -> float:
        """
        Получить цену за конкретную ночь с учетом сезонности.
        
        Args:
            room: Номер
            date: Дата
            
        Returns:
            float: Цена за ночь
        """
        coefficient = self.seasonal_coefficients.get(date.month, 1.0)
        return round(room.price_per_night * coefficient, 2)