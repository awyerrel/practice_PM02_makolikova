# Система управления бронированиями отелей
## Описание
Реализация сервисного слоя для системы управления бронированиями отелей с поддержкой мультиязычности (английский и русский языки).
**Вариант 10: Мультиязычность (Internationalization + Factory)**
## Архитектура
- **Domain Models**: Базовые сущности (Hotel, Room, Booking)
- **Repositories**: Абстракция доступа к данным (In-Memory)
- **Service Layer**: Бизнес-логика с поддержкой локализации
- **DTO**: Data Transfer Objects для передачи данных между слоями
- **Unit of Work**: Управление транзакциями
- **Factory Pattern**: Создание локализованных сообщений
## Структура проекта
booking_system/
├── src/
│ ├── domain/
│ │ ├── models.py # Сущности (Hotel, Room, Booking)
│ │ └── exceptions.py # Кастомные исключения
│ ├── services/
│ │ ├── hotel_service.py
│ │ ├── booking_service.py
│ │ └── pricing_service.py
│ ├── repositories/
│ │ ├── base.py # Абстрактный репозиторий
│ │ ├── hotel_repo.py
│ │ ├── room_repo.py
│ │ └── booking_repo.py
│ ├── dto/
│ │ ├── hotel_dto.py
│ │ ├── room_dto.py
│ │ └── booking_dto.py
│ ├── uow/
│ │ └── unit_of_work.py
│ └── config.py
├── tests/
│ ├── test_hotel_service.py
│ ├── test_booking_service.py
│ └── conftest.py
├── requirements.txt
├── pytest.ini
└── README.md
## Установка
```bash
pip install -r requirements.txt
Запуск тестов
bash
pytest
Поддерживаемые языки
English (en)
Русский (ru)
Использование
python
from src.uow.unit_of_work import UnitOfWork
from src.services.booking_service import BookingService
from src.services.pricing_service import PricingService
from src.dto.booking_dto import BookingCreateDTO
from datetime import date
uow = UnitOfWork()
pricing = PricingService()
booking_service = BookingService(uow, pricing)
dto = BookingCreateDTO(
    room_id=1,
    guest_name="Иван Петров",
    guest_email="ivan@example.com",
    check_in=date(2026, 6, 15),
    check_out=date(2026, 6, 20),
    locale="ru"
)
result = booking_service.create(dto)
print(result.message)  # "Бронирование 1 успешно создано"
Технологии
Python 3.10+
Pydantic V2
pytest + pytest-cov
Type Hints
PEP 8
Паттерны проектирования
Repository: Абстракция доступа к данным
Service Layer: Инкапсуляция бизнес-логики
Unit of Work: Управление транзакциями
DTO: Изоляция слоев
Factory: Создание локализованных сообщений
Strategy: Алгоритмы ценообразования
Dependency Injection: Слабая связанность