markdown
# Спецификация сервиса валидации заказов

## Бизнес-правила

### Правило 1: Ограничение суммы заказа
- total_amount > 0 И total_amount < 1_000_000
- Ошибка: "Order amount must be between 0 and 1,000,000"

### Правило 2: Лимит для новых пользователей
- Если created_at < 7 дней назад → total_amount <= 15_000
- Ошибка: "New users (created < 7 days) cannot order more than 15,000"

### Правило 3: Ограничение количества позиций
- len(items) <= 50
- Ошибка: "Order cannot contain more than 50 items"

### Правило 4: Правила для алкоголя
- Если есть товар с category="Alcohol":
  - age_verified == True
  - Время заказа между 08:00 и 23:00
- Ошибки:
  - "Alcohol requires age verification"
  - "Alcohol can only be ordered between 08:00 and 23:00"

### Правило 5: Расчет риск-скора
- Базовое значение: 0.0
- Если total_amount > 100_000 → risk_score = 0.9
- Если email менялся за последний час → risk_score += 0.2 (не более 1.0)
- Если страна доставки != страна кошелька → risk_score += 0.3 (не более 1.0)

## Примеры заказов

### Корректный заказ
```json
{
  "order_id": "ORD-001",
  "user_id": "USR-001",
  "items": [
    {"product_id": "P001", "quantity": 2, "price": 250, "category": "Food"}
  ],
  "total_amount": 500,
  "order_time": "2026-06-16T12:00:00Z",
  "created_at": "2026-06-09T10:00:00Z",
  "age_verified": false,
  "delivery_country": "Russia",
  "wallet_country": "Russia"
}
Результат: valid=True, reasons=[], risk_score=0.0

Некорректный заказ (сумма = 0)
json
{
  "order_id": "ORD-005",
  "user_id": "USR-005",
  "items": [],
  "total_amount": 0,
  "order_time": "2026-06-16T12:00:00Z",
  "created_at": "2026-06-01T10:00:00Z",
  "age_verified": false,
  "delivery_country": "Russia",
  "wallet_country": "Russia"
}
Результат: valid=False, reasons=["Order amount must be between 0 and 1,000,000"], risk_score=0.0

Некорректный заказ (новый пользователь)
json
{
  "order_id": "ORD-006",
  "user_id": "USR-006",
  "items": [
    {"product_id": "P006", "quantity": 1, "price": 20000, "category": "Electronics"}
  ],
  "total_amount": 20000,
  "order_time": "2026-06-16T12:00:00Z",
  "created_at": "2026-06-15T10:00:00Z",
  "age_verified": false,
  "delivery_country": "Russia",
  "wallet_country": "Russia"
}
Результат: valid=False, reasons=["New users (created < 7 days) cannot order more than 15,000"], risk_score=0.0

Decision Table
ID	total_amount	days_since_created	items_count	has_alcohol	age_verified	order_hour	email_changed	countries_match	valid	risk_score
D1	500	10	5	false	false	12	false	true	true	0.0
D2	0	10	5	false	false	12	false	true	false	0.0
D3	1_500_000	10	5	false	false	12	false	true	false	0.0
D4	20_000	5	5	false	false	12	false	true	false	0.0
D5	10_000	7	5	false	false	12	false	true	true	0.0
D6	500	10	51	false	false	12	false	true	false	0.0
D7	500	10	5	true	false	12	false	true	false	0.0
D8	500	10	5	true	true	7	false	true	false	0.0
D9	500	10	5	true	true	23	false	true	true	0.0
D10	150_000	10	5	false	false	12	false	true	true	0.9
D11	500	10	5	false	false	12	true	true	true	0.2
D12	500	10	5	false	false	12	false	false	true	0.3
Свойства системы (для property-based тестов)
Монотонность риск-скора: При увеличении суммы заказа риск-скор не убывает

Инвариант валидности: Если valid=False, то есть хотя бы одна причина в reasons

Идемпотентность: Повторный вызов дает тот же результат