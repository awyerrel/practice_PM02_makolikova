import pytest

from src.memory_repositories import (
    InMemoryClientRepository,
    InMemoryMembershipRepository,
    InMemoryWorkoutRepository,
    InMemoryBookingRepository
)

from src.service import FitnessClubService

from src.exceptions import (
    ClientNotFound,
    MembershipFrozen,
    WorkoutFull
)


@pytest.fixture
def service():
    return FitnessClubService(
        InMemoryClientRepository(),
        InMemoryMembershipRepository(),
        InMemoryWorkoutRepository(),
        InMemoryBookingRepository()
    )


def test_booking_success(service):
    service.register_client(1, "Ivan", "ivan@test.ru", "123")
    service.buy_membership(1, 1)
    service.create_workout(1, "CrossFit", "Coach", 5)
    
    booking = service.book_workout(1, 1)
    assert booking.client_id == 1


def test_client_not_found(service):
    service.create_workout(1, "CrossFit", "Coach", 5)
    
    with pytest.raises(ClientNotFound):
        service.book_workout(999, 1)


def test_membership_frozen(service):
    service.register_client(1, "Ivan", "ivan@test.ru", "123")
    service.buy_membership(1, 1)
    service.freeze_membership(1)
    service.create_workout(1, "CrossFit", "Coach", 5)
    
    with pytest.raises(MembershipFrozen):
        service.book_workout(1, 1)


def test_workout_full(service):
    service.register_client(1, "Ivan", "ivan@test.ru", "123")
    service.buy_membership(1, 1)
    service.create_workout(1, "CrossFit", "Coach", 1)
    service.book_workout(1, 1)
    
    service.register_client(2, "Petr", "petr@test.ru", "321")
    service.buy_membership(2, 2)
    
    with pytest.raises(WorkoutFull):
        service.book_workout(2, 1)


def test_discount(service):
    assert service.calculate_discount(25) == 15