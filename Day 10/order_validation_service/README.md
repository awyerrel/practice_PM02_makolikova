markdown
# Сервис валидации заказов

## Описание

Сервис предоставляет функцию `validate_order(order: dict) -> dict`, которая проверяет заказ на соответствие бизнес-правилам и вычисляет риск-скор.

## Установка

```bash
pip install -r requirements.txt
Запуск тестов
bash
# Все тесты
pytest tests/ -v

# Только параметризованные тесты
pytest tests/test_validate_order.py -v

# Только property-based тесты
pytest tests/test_properties.py -v

# С покрытием
pytest tests/ --cov=src --cov-report=html

# В несколько потоков
pytest tests/ -n auto
Структура проекта
text
order_validation_service/
├── specification.md          # Спецификация с правилами
├── test_cases.md            # Таблица тест-кейсов
├── requirements.txt         # Зависимости
├── README.md               # Этот файл
├── src/
│   ├── __init__.py
│   └── fake_validator.py   # Эталонная реализация
└── tests/
    ├── __init__.py
    ├── conftest.py         # Фикстуры
    ├── test_validate_order.py  # Параметризованные тесты
    └── test_properties.py      # Property-based тесты
Проверяемые свойства
Монотонность риск-скора: при увеличении суммы риск не убывает

Инвариант валидности: если valid=False, есть причина в reasons

Идемпотентность: повторные вызовы дают одинаковый результат

Корректность риск-скора: всегда в диапазоне [0, 1]

Режим хаоса
Для проверки устойчивости тестов можно включить режим хаоса:

python
validator = FakeValidator(chaos_mode=True)
# 5% запросов вернут случайный результат
Бизнес-правила
Правило 1: Ограничение суммы заказа
total_amount > 0 И total_amount < 1_000_000

Ошибка: "Order amount must be between 0 and 1,000,000"

Правило 2: Лимит для новых пользователей
Если created_at < 7 дней назад → total_amount <= 15_000

Ошибка: "New users (created < 7 days) cannot order more than 15,000"

Правило 3: Ограничение количества позиций
len(items) <= 50

Ошибка: "Order cannot contain more than 50 items"

Правило 4: Правила для алкоголя
Если есть товар с category="Alcohol":

age_verified == True

Время заказа между 08:00 и 23:00

Ошибки:

"Alcohol requires age verification"

"Alcohol can only be ordered between 08:00 and 23:00"

Правило 5: Расчет риск-скора
Базовое значение: 0.0

Если total_amount > 100_000 → risk_score = 0.9

Если email менялся за последний час → risk_score += 0.2 (не более 1.0)

Если страна доставки != страна кошелька → risk_score += 0.3 (не более 1.0)

Интерпретация результатов
Все тесты зеленые → спецификация корректна, реализация следует правилам

Падение тестов → проблема в спецификации или реализации

Property-based тесты находят крайние случаи → нужно уточнить правила

Пример использования
python
from src.fake_validator import FakeValidator

validator = FakeValidator()

order = {
    "order_id": "ORD-001",
    "user_id": "USR-001",
    "items": [
        {"product_id": "P001", "quantity": 2, "price": 250, "category": "Food"}
    ],
    "total_amount": 500,
    "order_time": "2026-06-16T12:00:00Z",
    "created_at": "2026-06-09T10:00:00Z",
    "age_verified": False,
    "delivery_country": "Russia",
    "wallet_country": "Russia"
}

result = validator.validate_order(order)
print(result)
# {'valid': True, 'reasons': [], 'risk_score': 0.0}
Требования
Python 3.8+

pytest 7.4.0+

hypothesis 6.88.0+

pydantic 2.0.0+