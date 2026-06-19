# Тест-кейсы для валидации заказов

## Группа 1: Сумма заказа (Rule 1)

| ID | Входные данные | Ожидаемый результат |
|----|---------------|---------------------|
| TC-01 | total_amount=0 | valid=False, reasons=["Order amount must be between 0 and 1,000,000"] |
| TC-02 | total_amount=0.01 | valid=True, reasons=[] |
| TC-03 | total_amount=999999.99 | valid=True, reasons=[] |
| TC-04 | total_amount=1000000 | valid=False, reasons=["Order amount must be between 0 and 1,000,000"] |

## Группа 2: Новые пользователи (Rule 2)

| ID | Входные данные | Ожидаемый результат |
|----|---------------|---------------------|
| TC-05 | created_at=7 дней назад, total_amount=15000 | valid=True |
| TC-06 | created_at=6.9 дней, total_amount=15000 | valid=True |
| TC-07 | created_at=6.9 дней, total_amount=15001 | valid=False, reasons=["New users (created < 7 days) cannot order more than 15,000"] |

## Группа 3: Количество позиций (Rule 3)

| ID | Входные данные | Ожидаемый результат |
|----|---------------|---------------------|
| TC-08 | items=50 штук | valid=True |
| TC-09 | items=51 штук | valid=False, reasons=["Order cannot contain more than 50 items"] |

## Группа 4: Алкоголь (Rule 4)

| ID | Входные данные | Ожидаемый результат |
|----|---------------|---------------------|
| TC-10 | has_alcohol=true, age_verified=false | valid=False, reasons=["Alcohol requires age verification"] |
| TC-11 | has_alcohol=true, order_time=07:59 | valid=False, reasons=["Alcohol can only be ordered between 08:00 and 23:00"] |
| TC-12 | has_alcohol=true, order_time=08:00 | valid=True |
| TC-13 | has_alcohol=true, order_time=23:00 | valid=True |

## Группа 5: Риск-скор (Rule 5)

| ID | Входные данные | Ожидаемый risk_score |
|----|---------------|---------------------|
| TC-14 | total_amount=100000.01 | 0.9 |
| TC-15 | total_amount=100000 | 0.0 |
| TC-16 | email_changed_at < 1 час | 0.2 |
| TC-17 | email_changed_at > 1 час | 0.0 |
| TC-18 | delivery_country != wallet_country | 0.3 |
| TC-19 | total_amount=150000 + email_changed + country_mismatch | 1.0 |

## Группа 6: Комбинации

| ID | Входные данные | Ожидаемый результат |
|----|---------------|---------------------|
| TC-20 | new_user + has_alcohol + age_verified=true + order_time=14:00 | valid=True |
| TC-21 | new_user + has_alcohol + age_verified=false | valid=False |
| TC-22 | new_user + total_amount=20000 | valid=False |
| TC-23 | total_amount=150000 + has_alcohol + age_verified=true | valid=True, risk_score=0.9 |