# src/core/events.py
"""
Доменные события для системы логистики и бронирования

Реализует паттерны:
- Domain Events: события, происходящие в доменной модели
- Event Bus: шина для публикации и подписки на события
- Event Handlers: обработчики событий для выполнения побочных действий

Используется для:
- Логирования важных действий
- Уведомления других сервисов
- Асинхронной обработки
- Аудита
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Type, Union
from enum import Enum
import json
import uuid
from abc import ABC, abstractmethod


# --- Базовые классы для событий ---

class EventType(Enum):
    """Типы доменных событий"""
    # События маршрутов
    ROUTE_CREATED = "route.created"
    ROUTE_UPDATED = "route.updated"
    ROUTE_DELETED = "route.deleted"
    ROUTE_OPTIMIZED = "route.optimized"
    ROUTE_CALCULATED = "route.calculated"
    
    # События локаций
    LOCATION_CREATED = "location.created"
    LOCATION_UPDATED = "location.updated"
    LOCATION_DELETED = "location.deleted"
    
    # События отелей
    HOTEL_CREATED = "hotel.created"
    HOTEL_UPDATED = "hotel.updated"
    HOTEL_DELETED = "hotel.deleted"
    HOTEL_BOOKED = "hotel.booked"
    HOTEL_CANCELLED = "hotel.cancelled"
    
    # События бронирования
    BOOKING_CREATED = "booking.created"
    BOOKING_UPDATED = "booking.updated"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_CONFIRMED = "booking.confirmed"
    
    # Системные события
    ERROR_OCCURRED = "system.error"
    PERFORMANCE_WARNING = "system.performance_warning"
    INTEGRATION_EVENT = "system.integration"


@dataclass
class DomainEvent(ABC):
    """Базовый класс для доменных событий"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(default=EventType.INTEGRATION_EVENT)
    occurred_at: datetime = field(default_factory=datetime.now)
    source: str = ""
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать событие в словарь"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            'occurred_at': self.occurred_at.isoformat(),
            'source': self.source,
            'version': self.version
        }
    
    def to_json(self) -> str:
        """Преобразовать событие в JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        """Создать событие из словаря"""
        return cls(
            event_id=data.get('event_id', str(uuid.uuid4())),
            event_type=EventType(data.get('event_type', 'system.integration')),
            occurred_at=datetime.fromisoformat(data['occurred_at']) if 'occurred_at' in data else datetime.now(),
            source=data.get('source', ''),
            version=data.get('version', 1)
        )


# --- Конкретные события ---

@dataclass
class RouteCreatedEvent(DomainEvent):
    """Событие создания маршрута"""
    route_id: int = 0
    start_location_id: int = 0
    end_location_id: int = 0
    total_distance: float = 0.0
    total_duration: int = 0
    segments_count: int = 0
    transport_types: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.event_type = EventType.ROUTE_CREATED
        self.source = "RouteService"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'route_id': self.route_id,
            'start_location_id': self.start_location_id,
            'end_location_id': self.end_location_id,
            'total_distance': self.total_distance,
            'total_duration': self.total_duration,
            'segments_count': self.segments_count,
            'transport_types': self.transport_types
        })
        return data


@dataclass
class RouteOptimizedEvent(DomainEvent):
    """Событие оптимизации маршрута"""
    route_id: int = 0
    original_distance: float = 0.0
    optimized_distance: float = 0.0
    original_duration: int = 0
    optimized_duration: int = 0
    hotels_visited: List[int] = field(default_factory=list)
    optimization_percent: float = 0.0
    
    def __post_init__(self):
        self.event_type = EventType.ROUTE_OPTIMIZED
        self.source = "RouteOptimizationService"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'route_id': self.route_id,
            'original_distance': self.original_distance,
            'optimized_distance': self.optimized_distance,
            'original_duration': self.original_duration,
            'optimized_duration': self.optimized_duration,
            'hotels_visited': self.hotels_visited,
            'optimization_percent': self.optimization_percent
        })
        return data


@dataclass
class HotelBookedEvent(DomainEvent):
    """Событие бронирования отеля"""
    hotel_id: int = 0
    hotel_name: str = ""
    guest_name: str = ""
    check_in_date: datetime = field(default_factory=datetime.now)
    check_out_date: datetime = field(default_factory=datetime.now)
    guests_count: int = 1
    total_price: float = 0.0
    booking_reference: str = ""
    
    def __post_init__(self):
        self.event_type = EventType.HOTEL_BOOKED
        self.source = "BookingService"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'hotel_id': self.hotel_id,
            'hotel_name': self.hotel_name,
            'guest_name': self.guest_name,
            'check_in_date': self.check_in_date.isoformat() if isinstance(self.check_in_date, datetime) else self.check_in_date,
            'check_out_date': self.check_out_date.isoformat() if isinstance(self.check_out_date, datetime) else self.check_out_date,
            'guests_count': self.guests_count,
            'total_price': self.total_price,
            'booking_reference': self.booking_reference
        })
        return data


@dataclass
class LocationCreatedEvent(DomainEvent):
    """Событие создания локации"""
    location_id: int = 0
    location_name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    city: str = ""
    country: str = ""
    
    def __post_init__(self):
        self.event_type = EventType.LOCATION_CREATED
        self.source = "LocationService"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'location_id': self.location_id,
            'location_name': self.location_name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'city': self.city,
            'country': self.country
        })
        return data


@dataclass
class BookingCreatedEvent(DomainEvent):
    """Событие создания бронирования"""
    booking_id: int = 0
    room_id: int = 0
    hotel_id: int = 0
    guest_name: str = ""
    check_in_date: datetime = field(default_factory=datetime.now)
    check_out_date: datetime = field(default_factory=datetime.now)
    total_price: float = 0.0
    status: str = "pending"
    
    def __post_init__(self):
        self.event_type = EventType.BOOKING_CREATED
        self.source = "BookingService"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'booking_id': self.booking_id,
            'room_id': self.room_id,
            'hotel_id': self.hotel_id,
            'guest_name': self.guest_name,
            'check_in_date': self.check_in_date.isoformat() if isinstance(self.check_in_date, datetime) else self.check_in_date,
            'check_out_date': self.check_out_date.isoformat() if isinstance(self.check_out_date, datetime) else self.check_out_date,
            'total_price': self.total_price,
            'status': self.status
        })
        return data


@dataclass
class PerformanceWarningEvent(DomainEvent):
    """Событие предупреждения о производительности"""
    operation: str = ""
    execution_time_ms: float = 0.0
    threshold_ms: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.PERFORMANCE_WARNING
        self.source = "PerformanceMonitor"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'operation': self.operation,
            'execution_time_ms': self.execution_time_ms,
            'threshold_ms': self.threshold_ms,
            'context': self.context
        })
        return data


@dataclass
class ErrorOccurredEvent(DomainEvent):
    """Событие возникновения ошибки"""
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = EventType.ERROR_OCCURRED
        self.source = "System"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'error_type': self.error_type,
            'error_message': self.error_message,
            'stack_trace': self.stack_trace,
            'context': self.context
        })
        return data


# --- Обработчики событий ---

class EventHandler(ABC):
    """Базовый класс для обработчиков событий"""
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Обработать событие"""
        pass
    
    @abstractmethod
    def can_handle(self, event: DomainEvent) -> bool:
        """Может ли обработчик обработать событие"""
        pass


class LoggingEventHandler(EventHandler):
    """Обработчик для логирования событий"""
    
    def __init__(self, logger=None):
        self.logger = logger or self._default_logger
    
    def _default_logger(self, message: str):
        """Логгер по умолчанию"""
        print(f"[EVENT] {message}")
    
    def handle(self, event: DomainEvent) -> None:
        """Логировать событие"""
        event_data = event.to_dict()
        self.logger(f"Event: {event.event_type.value} - {event_data}")
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Может обрабатывать все события"""
        return True


class NotificationEventHandler(EventHandler):
    """Обработчик для отправки уведомлений"""
    
    def __init__(self, notification_service=None):
        self.notification_service = notification_service or self._default_notification
    
    def _default_notification(self, message: str):
        """Уведомление по умолчанию"""
        print(f"[NOTIFICATION] {message}")
    
    def handle(self, event: DomainEvent) -> None:
        """Отправить уведомление"""
        if isinstance(event, HotelBookedEvent):
            self.notification_service(
                f"Новое бронирование: {event.hotel_name}, Гость: {event.guest_name}"
            )
        elif isinstance(event, RouteOptimizedEvent):
            self.notification_service(
                f"Маршрут {event.route_id} оптимизирован на {event.optimization_percent:.1f}%"
            )
        elif isinstance(event, BookingCreatedEvent):
            self.notification_service(
                f"Создано бронирование #{event.booking_id} для {event.guest_name}"
            )
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Обрабатывает только определенные события"""
        return isinstance(event, (HotelBookedEvent, RouteOptimizedEvent, BookingCreatedEvent))


class AuditEventHandler(EventHandler):
    """Обработчик для аудита"""
    
    def __init__(self, audit_storage=None):
        self.audit_storage = audit_storage or self._default_storage
        self.audit_log = []
    
    def _default_storage(self, event_data: Dict[str, Any]):
        """Хранилище по умолчанию"""
        self.audit_log.append(event_data)
        print(f"[AUDIT] {event_data}")
    
    def handle(self, event: DomainEvent) -> None:
        """Сохранить событие для аудита"""
        event_data = event.to_dict()
        self.audit_storage(event_data)
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Обрабатывает все события"""
        return True
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Получить лог аудита"""
        return self.audit_log


class MetricEventHandler(EventHandler):
    """Обработчик для сбора метрик"""
    
    def __init__(self, metrics_collector=None):
        self.metrics_collector = metrics_collector or self._default_collector
        self.metrics = {}
    
    def _default_collector(self, metric_name: str, value: float):
        """Коллектор метрик по умолчанию"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
        print(f"[METRIC] {metric_name}: {value}")
    
    def handle(self, event: DomainEvent) -> None:
        """Собрать метрики"""
        if isinstance(event, RouteCreatedEvent):
            self.metrics_collector(
                "route.total_distance",
                event.total_distance
            )
            self.metrics_collector(
                "route.segments_count",
                event.segments_count
            )
        elif isinstance(event, RouteOptimizedEvent):
            self.metrics_collector(
                "route.optimization_percent",
                event.optimization_percent
            )
        elif isinstance(event, PerformanceWarningEvent):
            self.metrics_collector(
                "performance.execution_time",
                event.execution_time_ms
            )
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Обрабатывает только определенные события"""
        return isinstance(event, (RouteCreatedEvent, RouteOptimizedEvent, PerformanceWarningEvent))
    
    def get_metrics(self) -> Dict[str, List[float]]:
        """Получить собранные метрики"""
        return self.metrics


class EmailNotificationEventHandler(EventHandler):
    """Обработчик для email уведомлений"""
    
    def __init__(self, email_service=None):
        self.email_service = email_service or self._default_email
    
    def _default_email(self, to: str, subject: str, body: str):
        """Email сервис по умолчанию"""
        print(f"[EMAIL] To: {to}")
        print(f"[EMAIL] Subject: {subject}")
        print(f"[EMAIL] Body: {body}")
        print("-" * 50)
    
    def handle(self, event: DomainEvent) -> None:
        """Отправить email"""
        if isinstance(event, BookingCreatedEvent):
            self.email_service(
                to="guest@example.com",
                subject=f"Подтверждение бронирования #{event.booking_id}",
                body=f"""
                Уважаемый(ая) {event.guest_name}!
                
                Ваше бронирование #{event.booking_id} подтверждено.
                Дата заезда: {event.check_in_date}
                Дата выезда: {event.check_out_date}
                Сумма: {event.total_price} руб.
                
                Спасибо, что выбрали нас!
                """
            )
        elif isinstance(event, HotelBookedEvent):
            self.email_service(
                to="hotel@example.com",
                subject=f"Новое бронирование в {event.hotel_name}",
                body=f"""
                Уважаемая администрация!
                
                Поступило новое бронирование:
                Отель: {event.hotel_name}
                Гость: {event.guest_name}
                Дата заезда: {event.check_in_date}
                Дата выезда: {event.check_out_date}
                Количество гостей: {event.guests_count}
                Сумма: {event.total_price} руб.
                """
            )
    
    def can_handle(self, event: DomainEvent) -> bool:
        """Обрабатывает только события бронирования"""
        return isinstance(event, (BookingCreatedEvent, HotelBookedEvent))


# --- Шина событий ---

class EventBus:
    """
    Шина событий для публикации и подписки
    
    Реализует паттерн Observer для слабосвязанной обработки событий
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[DomainEvent] = []
    
    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Подписаться на событие
        
        Args:
            event_type: Тип события
            handler: Обработчик события
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """
        Подписаться на все события
        
        Args:
            handler: Обработчик события
        """
        self._global_handlers.append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Отписаться от события
        
        Args:
            event_type: Тип события
            handler: Обработчик события
        """
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h != handler
            ]
    
    def publish(self, event: DomainEvent) -> None:
        """
        Опубликовать событие
        
        Args:
            event: Событие для публикации
        """
        # Сохраняем историю
        self._event_history.append(event)
        
        # Обрабатываем глобальными обработчиками
        for handler in self._global_handlers:
            if handler.can_handle(event):
                try:
                    handler.handle(event)
                except Exception as e:
                    print(f"Error in global handler {handler.__class__.__name__}: {e}")
        
        # Обрабатываем специфическими обработчиками
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    handler.handle(event)
                except Exception as e:
                    print(f"Error in handler {handler.__class__.__name__}: {e}")
    
    def publish_all(self, events: List[DomainEvent]) -> None:
        """
        Опубликовать несколько событий
        
        Args:
            events: Список событий
        """
        for event in events:
            self.publish(event)
    
    def get_history(self, event_type: Optional[EventType] = None) -> List[DomainEvent]:
        """
        Получить историю событий
        
        Args:
            event_type: Фильтр по типу события
        
        Returns:
            Список событий
        """
        if event_type:
            return [e for e in self._event_history if e.event_type == event_type]
        return self._event_history.copy()
    
    def clear_history(self) -> None:
        """Очистить историю событий"""
        self._event_history.clear()
    
    def get_handlers_count(self) -> int:
        """Получить количество зарегистрированных обработчиков"""
        count = len(self._global_handlers)
        for handlers in self._handlers.values():
            count += len(handlers)
        return count


# --- Декораторы для событий ---

def event_handler(event_type: EventType):
    """
    Декоратор для регистрации обработчиков событий
    
    Args:
        event_type: Тип события
    
    Example:
        @event_handler(EventType.ROUTE_CREATED)
        def on_route_created(event: RouteCreatedEvent):
            print(f"Route {event.route_id} created")
    """
    def decorator(func):
        func._event_type = event_type
        func._is_event_handler = True
        return func
    return decorator


# --- Контекстный менеджер для событий ---

class EventContext:
    """
    Контекстный менеджер для сбора и публикации событий
    
    Example:
        with EventContext() as context:
            # Выполняем операции
            context.add_event(RouteCreatedEvent(...))
            # События будут опубликованы автоматически
    """
    
    def __init__(self, event_bus: Optional[EventBus] = None):
        self.event_bus = event_bus or get_default_event_bus()
        self.events: List[DomainEvent] = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:  # Если не было исключений
            self.publish_all()
    
    def add_event(self, event: DomainEvent) -> None:
        """Добавить событие в контекст"""
        self.events.append(event)
    
    def add_events(self, events: List[DomainEvent]) -> None:
        """Добавить несколько событий"""
        self.events.extend(events)
    
    def publish_all(self) -> None:
        """Опубликовать все события"""
        if self.events:
            self.event_bus.publish_all(self.events)
            self.events.clear()


# --- Глобальная шина событий ---

_event_bus: Optional[EventBus] = None


def get_default_event_bus() -> EventBus:
    """Получить глобальную шину событий (Singleton)"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        # Регистрируем обработчики по умолчанию
        _event_bus.subscribe_all(LoggingEventHandler())
        _event_bus.subscribe_all(AuditEventHandler())
        _event_bus.subscribe(EventType.BOOKING_CREATED, EmailNotificationEventHandler())
        _event_bus.subscribe(EventType.HOTEL_BOOKED, NotificationEventHandler())
        _event_bus.subscribe(EventType.ROUTE_OPTIMIZED, MetricEventHandler())
    return _event_bus


def reset_event_bus() -> None:
    """Сбросить глобальную шину событий (для тестов)"""
    global _event_bus
    _event_bus = None


# --- Пример использования ---

def example_usage():
    """Пример использования системы событий"""
    
    # Получаем шину событий
    event_bus = get_default_event_bus()
    
    # Создаем событие
    route_event = RouteCreatedEvent(
        route_id=123,
        start_location_id=1,
        end_location_id=2,
        total_distance=634.0,
        total_duration=480,
        segments_count=1,
        transport_types=["car"]
    )
    
    # Публикуем событие
    event_bus.publish(route_event)
    
    # Создаем событие бронирования
    booking_event = BookingCreatedEvent(
        booking_id=456,
        room_id=10,
        hotel_id=5,
        guest_name="Иван Петров",
        check_in_date=datetime(2026, 7, 1),
        check_out_date=datetime(2026, 7, 7),
        total_price=35000.0,
        status="confirmed"
    )
    
    # Публикуем с использованием контекста
    with EventContext(event_bus) as context:
        context.add_event(booking_event)
        context.add_event(RouteOptimizedEvent(
            route_id=123,
            original_distance=800.0,
            optimized_distance=634.0,
            original_duration=600,
            optimized_duration=480,
            hotels_visited=[1, 2, 3],
            optimization_percent=20.75
        ))
    
    print("\n" + "="*50)
    print("История событий:")
    for event in event_bus.get_history():
        print(f"  - {event.event_type.value}: {event.event_id}")
    
    # Получаем метрики
    metric_handler = None
    for handler in event_bus._handlers.get(EventType.ROUTE_OPTIMIZED, []):
        if isinstance(handler, MetricEventHandler):
            metric_handler = handler
            break
    
    if metric_handler:
        print("\nМетрики:")
        for name, values in metric_handler.get_metrics().items():
            print(f"  {name}: {values}")
    
    # Получаем аудит
    audit_handler = None
    for handler in event_bus._global_handlers:
        if isinstance(handler, AuditEventHandler):
            audit_handler = handler
            break
    
    if audit_handler:
        print("\nЛог аудита:")
        for entry in audit_handler.get_audit_log():
            print(f"  - {entry['event_type']}: {entry['event_id']}")
    
    return event_bus


if __name__ == "__main__":
    # Запуск примера
    example_usage()