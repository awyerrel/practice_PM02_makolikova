"""
FakeValidator - эталонная реализация для тестирования
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
from pydantic import BaseModel, Field, validator, ValidationError
from enum import Enum


class Category(str, Enum):
    FOOD = "Food"
    ELECTRONICS = "Electronics"
    CLOTHING = "Clothing"
    ALCOHOL = "Alcohol"
    BOOKS = "Books"
    OTHER = "Other"


class Item(BaseModel):
    product_id: str
    quantity: int
    price: float
    category: Category


class OrderInput(BaseModel):
    order_id: str
    user_id: str
    items: List[Item] = []
    total_amount: float
    order_time: datetime
    created_at: Optional[datetime] = None
    age_verified: bool = False
    email_changed_at: Optional[datetime] = None
    delivery_country: str
    wallet_country: Optional[str] = None


class FakeValidator:
    """Фейковая реализация валидатора"""

    def __init__(self, chaos_mode: bool = False, delay_seconds: float = 0.0):
        self.chaos_mode = chaos_mode
        self.delay_seconds = delay_seconds
        self._call_count = 0

    def validate_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Основной метод валидации"""
        self._call_count += 1

        # Режим хаоса
        if self.chaos_mode and random.random() < 0.05:
            return {
                "valid": random.choice([True, False]),
                "reasons": ["Chaos mode random error"],
                "risk_score": random.random()
            }

        # Валидация входных данных
        try:
            validated_order = OrderInput(**order)
        except ValidationError as e:
            return {
                "valid": False,
                "reasons": [f"Invalid input: {str(e)}"],
                "risk_score": 0.0
            }

        reasons = []

        # Rule 1: Проверка суммы
        if not (0 < validated_order.total_amount < 1_000_000):
            reasons.append("Order amount must be between 0 and 1,000,000")

        # Rule 2: Проверка новых пользователей
        if validated_order.created_at:
            days = (datetime.now() - validated_order.created_at).total_seconds() / (24 * 3600)
            if days < 7 and validated_order.total_amount > 15_000:
                reasons.append("New users (created < 7 days) cannot order more than 15,000")

        # Rule 3: Проверка количества позиций
        if len(validated_order.items) > 50:
            reasons.append("Order cannot contain more than 50 items")

        # Rule 4: Проверка алкоголя
        has_alcohol = any(item.category == Category.ALCOHOL for item in validated_order.items)
        if has_alcohol:
            if not validated_order.age_verified:
                reasons.append("Alcohol requires age verification")
            
            hour = validated_order.order_time.hour
            if not (8 <= hour <= 23):
                reasons.append("Alcohol can only be ordered between 08:00 and 23:00")

        # Определение валидности
        is_valid = len(reasons) == 0

        # Расчет риск-скора
        risk_score = self._calculate_risk_score(validated_order)

        return {
            "valid": is_valid,
            "reasons": reasons,
            "risk_score": risk_score
        }

    def _calculate_risk_score(self, order: OrderInput) -> float:
        """Расчет риск-скора"""
        risk_score = 0.0

        # Высокая сумма
        if order.total_amount > 100_000:
            risk_score = 0.9

        # Смена email
        if order.email_changed_at:
            hours = (datetime.now() - order.email_changed_at).total_seconds() / 3600
            if hours < 1:
                risk_score = min(1.0, risk_score + 0.2)

        # Несовпадение стран
        if order.wallet_country and order.delivery_country != order.wallet_country:
            risk_score = min(1.0, risk_score + 0.3)

        return risk_score