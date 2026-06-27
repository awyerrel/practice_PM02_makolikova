"""
Фикстуры для тестов
"""

import pytest
from datetime import datetime, timedelta
from src.fake_validator import FakeValidator


@pytest.fixture
def validator():
    """Стандартный валидатор"""
    return FakeValidator(chaos_mode=False, delay_seconds=0.0)


@pytest.fixture
def chaos_validator():
    """Валидатор с режимом хаоса"""
    return FakeValidator(chaos_mode=True, delay_seconds=0.0)


@pytest.fixture
def base_order():
    """Базовый корректный заказ"""
    return {
        "order_id": "ORD-001",
        "user_id": "USR-001",
        "items": [
            {"product_id": "P001", "quantity": 2, "price": 250, "category": "Food"}
        ],
        "total_amount": 500,
        "order_time": datetime(2026, 6, 16, 12, 0, 0),
        "created_at": datetime(2026, 6, 9, 10, 0, 0),
        "age_verified": False,
        "delivery_country": "Russia",
        "wallet_country": "Russia"
    }