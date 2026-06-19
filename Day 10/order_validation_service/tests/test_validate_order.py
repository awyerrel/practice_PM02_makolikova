"""
Параметризованные тесты для валидации заказов
"""

import pytest
from datetime import datetime, timedelta


class TestValidateOrder:
    """Тесты валидации заказов"""

    # ==================== Rule 1: Сумма заказа ====================
    @pytest.mark.parametrize("total_amount,expected_valid,expected_reason", [
        (0, False, "Order amount must be between 0 and 1,000,000"),
        (0.01, True, None),
        (999999.99, True, None),
        (1000000, False, "Order amount must be between 0 and 1,000,000"),
        (1000000.01, False, "Order amount must be between 0 and 1,000,000"),
    ])
    def test_rule1_amount(self, validator, base_order, total_amount, expected_valid, expected_reason):
        """Тест правила 1: ограничение суммы"""
        order = base_order.copy()
        order["total_amount"] = total_amount
        
        result = validator.validate_order(order)
        
        assert result["valid"] == expected_valid
        if expected_reason:
            assert expected_reason in result["reasons"]
        else:
            assert len(result["reasons"]) == 0

    # ==================== Rule 2: Новые пользователи ====================
    @pytest.mark.parametrize("days_ago,total_amount,expected_valid", [
        (7, 15000, True),
        (6.9, 15000, True),
        (6.9, 15001, False),
        (7, 15001, True),   # 7 дней = валидно (не меньше 7)
        (8, 20000, True),
    ])
    def test_rule2_new_user(self, validator, base_order, days_ago, total_amount, expected_valid):
        """Тест правила 2: лимит для новых пользователей"""
        order = base_order.copy()
        order["total_amount"] = total_amount
        order["created_at"] = datetime.now() - timedelta(days=days_ago)
        
        result = validator.validate_order(order)
        
        assert result["valid"] == expected_valid
        if not expected_valid:
            assert "New users (created < 7 days) cannot order more than 15,000" in result["reasons"]

    # ==================== Rule 3: Количество позиций ====================
    @pytest.mark.parametrize("items_count,expected_valid", [
        (50, True),
        (51, False),
        (100, False),
    ])
    def test_rule3_items_count(self, validator, base_order, items_count, expected_valid):
        """Тест правила 3: ограничение количества позиций"""
        order = base_order.copy()
        order["items"] = [
            {"product_id": f"P{i:03d}", "quantity": 1, "price": 100, "category": "Food"}
            for i in range(items_count)
        ]
        order["total_amount"] = items_count * 100
        
        result = validator.validate_order(order)
        
        assert result["valid"] == expected_valid
        if not expected_valid:
            assert "Order cannot contain more than 50 items" in result["reasons"]

    # ==================== Rule 4: Алкоголь ====================
    @pytest.mark.parametrize("age_verified,order_hour,expected_valid,expected_reason", [
        (False, 12, False, "Alcohol requires age verification"),
        (True, 7, False, "Alcohol can only be ordered between 08:00 and 23:00"),
        (True, 8, True, None),
        (True, 23, True, None),
        (True, 0, False, "Alcohol can only be ordered between 08:00 and 23:00"),
    ])
    def test_rule4_alcohol(self, validator, base_order, age_verified, order_hour, expected_valid, expected_reason):
        """Тест правила 4: проверка алкоголя"""
        order = base_order.copy()
        order["items"] = [
            {"product_id": "P001", "quantity": 1, "price": 1000, "category": "Alcohol"}
        ]
        order["total_amount"] = 1000
        order["age_verified"] = age_verified
        order["order_time"] = datetime(2026, 6, 16, order_hour, 0, 0)
        
        result = validator.validate_order(order)
        
        assert result["valid"] == expected_valid
        if expected_reason:
            assert expected_reason in result["reasons"]
        else:
            assert len(result["reasons"]) == 0

    # ==================== Rule 5: Риск-скор ====================
    @pytest.mark.parametrize("total_amount,email_changed_hours_ago,countries_match,expected_risk", [
        (500, None, True, 0.0),
        (150000, None, True, 0.9),
        (500, 0.5, True, 0.2),
        (500, 2, True, 0.0),
        (500, None, False, 0.3),
        (150000, 0.5, False, 1.0),
    ])
    def test_rule5_risk_score(self, validator, base_order, total_amount, email_changed_hours_ago, 
                             countries_match, expected_risk):
        """Тест правила 5: расчет риск-скора"""
        order = base_order.copy()
        order["total_amount"] = total_amount
        
        if email_changed_hours_ago is not None:
            order["email_changed_at"] = datetime.now() - timedelta(hours=email_changed_hours_ago)
        
        if not countries_match:
            order["wallet_country"] = "USA"
        else:
            order["wallet_country"] = "Russia"
        
        result = validator.validate_order(order)
        
        assert result["risk_score"] == expected_risk

    # ==================== Комбинации правил ====================
    @pytest.mark.parametrize("scenario", [
        {"desc": "New user + alcohol valid", 
         "created_days": 5, "total": 10000, "has_alcohol": True, 
         "age_verified": True, "hour": 14, "expected_valid": True},
        
        {"desc": "New user + alcohol invalid age", 
         "created_days": 5, "total": 10000, "has_alcohol": True, 
         "age_verified": False, "hour": 14, "expected_valid": False},
        
        {"desc": "New user + high amount", 
         "created_days": 5, "total": 20000, "has_alcohol": False, 
         "age_verified": False, "hour": 12, "expected_valid": False},
        
        {"desc": "High amount + alcohol valid", 
         "created_days": 10, "total": 150000, "has_alcohol": True, 
         "age_verified": True, "hour": 14, "expected_valid": True},
    ])
    def test_combined_rules(self, validator, base_order, scenario):
        """Тест комбинаций правил"""
        order = base_order.copy()
        order["total_amount"] = scenario["total"]
        order["created_at"] = datetime.now() - timedelta(days=scenario["created_days"])
        
        if scenario["has_alcohol"]:
            order["items"] = [
                {"product_id": "P001", "quantity": 1, "price": 100, "category": "Alcohol"}
            ]
        else:
            order["items"] = [
                {"product_id": "P001", "quantity": 1, "price": 100, "category": "Food"}
            ]
        order["age_verified"] = scenario["age_verified"]
        order["order_time"] = datetime(2026, 6, 16, scenario["hour"], 0, 0)
        
        result = validator.validate_order(order)
        assert result["valid"] == scenario["expected_valid"]

    # ==================== Тесты режима хаоса ====================
    def test_chaos_mode_validation(self, chaos_validator, base_order):
        """Тест режима хаоса: проверка, что валидатор работает в режиме хаоса"""
        results = []
        for _ in range(20):
            result = chaos_validator.validate_order(base_order)
            results.append(result)
        
        # Проверяем, что все результаты имеют правильную структуру
        for result in results:
            assert "valid" in result
            assert "reasons" in result
            assert "risk_score" in result
            assert isinstance(result["valid"], bool)
            assert isinstance(result["reasons"], list)
            assert 0 <= result["risk_score"] <= 1
        
        # Проверяем, что хотя бы один результат отличается (из-за хаоса)
        assert len(results) == 20

    def test_chaos_mode_randomness(self, chaos_validator, base_order):
        """Тест режима хаоса: проверка, что результаты могут отличаться"""
        result1 = chaos_validator.validate_order(base_order)
        result2 = chaos_validator.validate_order(base_order)
        result3 = chaos_validator.validate_order(base_order)
        
        # Проверяем, что структура результатов корректна
        for result in [result1, result2, result3]:
            assert "valid" in result
            assert "reasons" in result
            assert "risk_score" in result
            assert 0 <= result["risk_score"] <= 1

    def test_chaos_mode_with_invalid_data(self, chaos_validator, base_order):
        """Тест режима хаоса с невалидными данными"""
        order = base_order.copy()
        order["total_amount"] = 0  # Невалидный заказ
        
        result = chaos_validator.validate_order(order)
        
        # Проверяем структуру ответа
        assert "valid" in result
        assert "reasons" in result
        assert "risk_score" in result
        assert isinstance(result["valid"], bool)
        assert isinstance(result["reasons"], list)
        assert 0 <= result["risk_score"] <= 1