"""
Property-Based тесты с использованием Hypothesis
"""

import pytest
from hypothesis import given, strategies as st
from hypothesis.strategies import builds, datetimes, lists, sampled_from, floats
from datetime import datetime, timedelta
from src.fake_validator import FakeValidator, Category, Item, OrderInput


class TestProperties:
    """Property-based тесты"""

    @given(
        total_amount=st.floats(min_value=0.01, max_value=999999.99),
        days_ago=st.floats(min_value=0, max_value=30),
        items_count=st.integers(min_value=0, max_value=50),
        has_alcohol=st.booleans(),
        age_verified=st.booleans(),
        hour=st.integers(min_value=0, max_value=23),
    )
    def test_property_valid_orders_always_valid(self, total_amount, days_ago, items_count,
                                               has_alcohol, age_verified, hour):
        """Свойство: правильно сгенерированные заказы всегда валидны"""
        validator = FakeValidator()
        
        items = []
        for i in range(min(items_count, 10)):  # Ограничиваем для скорости
            category = Category.ALCOHOL if has_alcohol and i == 0 else Category.FOOD
            items.append(Item(
                product_id=f"P{i:03d}",
                quantity=1,
                price=total_amount / max(1, items_count),
                category=category
            ))
        
        order = OrderInput(
            order_id="ORD-001",
            user_id="USR-001",
            items=items,
            total_amount=total_amount,
            order_time=datetime(2026, 6, 16, hour, 0, 0),
            created_at=datetime.now() - timedelta(days=days_ago),
            age_verified=age_verified if has_alcohol else False,
            delivery_country="Russia",
            wallet_country="Russia"
        )
        
        result = validator.validate_order(order.dict())
        
        # Если заказ валидный по всем правилам, то valid=True
        is_valid_by_rules = (
            0 < total_amount < 1000000 and
            (days_ago >= 7 or total_amount <= 15000) and
            items_count <= 50 and
            (not has_alcohol or (age_verified and 8 <= hour <= 23))
        )
        
        if is_valid_by_rules:
            assert result["valid"] is True
            assert len(result["reasons"]) == 0

    def test_property_monotonic_risk_score(self):
        """Свойство: риск-скор не убывает при увеличении суммы"""
        validator = FakeValidator()
        base_order = {
            "order_id": "ORD-001",
            "user_id": "USR-001",
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Food"}],
            "order_time": datetime(2026, 6, 16, 12, 0, 0),
            "created_at": datetime(2026, 6, 1, 10, 0, 0),
            "age_verified": False,
            "delivery_country": "Russia",
            "wallet_country": "Russia"
        }
        
        amounts = [50000, 100000, 150000, 200000]
        risk_scores = []
        
        for amount in amounts:
            order = base_order.copy()
            order["total_amount"] = amount
            result = validator.validate_order(order)
            risk_scores.append(result["risk_score"])
        
        # Проверяем, что риск-скор не убывает
        for i in range(1, len(risk_scores)):
            assert risk_scores[i] >= risk_scores[i-1]

    def test_property_invariant_valid_has_reason(self):
        """Свойство: если valid=False, то есть хотя бы одна причина"""
        validator = FakeValidator()
        
        # Генерируем заведомо невалидные заказы
        invalid_orders = [
            {"total_amount": 0, "reason": "Order amount must be between 0 and 1,000,000"},
            {"total_amount": 1000000, "reason": "Order amount must be between 0 and 1,000,000"},
            {"items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}],
             "age_verified": False, "reason": "Alcohol requires age verification"},
        ]
        
        base_order = {
            "order_id": "ORD-001",
            "user_id": "USR-001",
            "order_time": datetime(2026, 6, 16, 12, 0, 0),
            "created_at": datetime(2026, 6, 1, 10, 0, 0),
            "delivery_country": "Russia",
            "wallet_country": "Russia"
        }
        
        for invalid in invalid_orders:
            order = base_order.copy()
            order.update(invalid)
            if "total_amount" not in order:
                order["total_amount"] = 500
            if "items" not in order:
                order["items"] = [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Food"}]
            
            result = validator.validate_order(order)
            assert result["valid"] is False
            assert len(result["reasons"]) > 0
            assert invalid["reason"] in result["reasons"]

    def test_property_idempotence(self):
        """Свойство: повторный вызов дает тот же результат"""
        validator = FakeValidator()
        
        order = {
            "order_id": "ORD-001",
            "user_id": "USR-001",
            "items": [{"product_id": "P001", "quantity": 2, "price": 250, "category": "Food"}],
            "total_amount": 500,
            "order_time": datetime(2026, 6, 16, 12, 0, 0),
            "created_at": datetime(2026, 6, 9, 10, 0, 0),
            "age_verified": False,
            "delivery_country": "Russia",
            "wallet_country": "Russia"
        }
        
        result1 = validator.validate_order(order)
        result2 = validator.validate_order(order)
        result3 = validator.validate_order(order)
        
        assert result1 == result2 == result3

    def test_property_risk_score_in_range(self):
        """Свойство: риск-скор всегда в диапазоне [0, 1]"""
        validator = FakeValidator()
        
        # Тестируем разные сценарии
        test_cases = [
            {"total_amount": 50, "email_changed_at": None, "wallet_country": "Russia"},
            {"total_amount": 150000, "email_changed_at": None, "wallet_country": "Russia"},
            {"total_amount": 50, "email_changed_at": datetime.now() - timedelta(minutes=30), 
             "wallet_country": "Russia"},
            {"total_amount": 50, "email_changed_at": None, "wallet_country": "USA"},
            {"total_amount": 150000, "email_changed_at": datetime.now() - timedelta(minutes=30), 
             "wallet_country": "USA"},
        ]
        
        base_order = {
            "order_id": "ORD-001",
            "user_id": "USR-001",
            "items": [{"product_id": "P001", "quantity": 1, "price": 100, "category": "Food"}],
            "order_time": datetime(2026, 6, 16, 12, 0, 0),
            "created_at": datetime(2026, 6, 1, 10, 0, 0),
            "age_verified": False,
            "delivery_country": "Russia",
        }
        
        for test in test_cases:
            order = base_order.copy()
            order.update(test)
            
            result = validator.validate_order(order)
            assert 0 <= result["risk_score"] <= 1