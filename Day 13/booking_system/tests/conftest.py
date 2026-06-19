import pytest
from datetime import date
from src.uow.unit_of_work import UnitOfWork
from src.services.booking_service import BookingService
from src.services.hotel_service import HotelService
from src.services.pricing_service import PricingService
from src.domain.models import Hotel, Room, Booking, BookingStatus


@pytest.fixture
def uow():
    """Фикстура: Unit of Work"""
    return UnitOfWork()


@pytest.fixture
def pricing_service():
    """Фикстура: Pricing Service"""
    return PricingService()


@pytest.fixture
def hotel_service(uow):
    """Фикстура: Hotel Service"""
    return HotelService(uow)


@pytest.fixture
def booking_service(uow, pricing_service):
    """Фикстура: Booking Service"""
    return BookingService(uow, pricing_service, min_hotel_rating=3.0)


@pytest.fixture
def sample_hotel(uow):
    """Фикстура: пример отеля"""
    hotel = Hotel(
        id=None,
        name="Grand Hotel",
        address="123 Main St, New York",
        phone="+1-555-123-4567",
        rating=4.5
    )
    return uow.hotels.add(hotel)


@pytest.fixture
def sample_room(uow, sample_hotel):
    """Фикстура: пример номера"""
    room = Room(
        id=None,
        hotel_id=sample_hotel.id,
        number="101",
        capacity=2,
        price_per_night=100.0,
        is_active=True,
        room_type="standard"
    )
    return uow.rooms.add(room)


@pytest.fixture
def sample_room_deluxe(uow, sample_hotel):
    """Фикстура: пример номера deluxe"""
    room = Room(
        id=None,
        hotel_id=sample_hotel.id,
        number="102",
        capacity=4,
        price_per_night=150.0,
        is_active=True,
        room_type="deluxe"
    )
    return uow.rooms.add(room)


@pytest.fixture
def sample_booking(uow, sample_room):
    """Фикстура: пример бронирования"""
    booking = Booking(
        id=None,
        room_id=sample_room.id,
        guest_name="John Doe",
        guest_email="john@example.com",
        check_in=date(2026, 6, 15),
        check_out=date(2026, 6, 20),
        total_price=500.0,
        status=BookingStatus.PENDING,
        locale="en"
    )
    return uow.bookings.add(booking)


@pytest.fixture
def sample_booking_confirmed(uow, sample_room):
    """Фикстура: подтвержденное бронирование"""
    booking = Booking(
        id=None,
        room_id=sample_room.id,
        guest_name="Jane Smith",
        guest_email="jane@example.com",
        check_in=date(2026, 7, 1),
        check_out=date(2026, 7, 5),
        total_price=400.0,
        status=BookingStatus.CONFIRMED,
        locale="en"
    )
    return uow.bookings.add(booking)