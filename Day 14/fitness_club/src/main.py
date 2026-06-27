<<<<<<< HEAD
from src.memory_repositories import (
    InMemoryClientRepository,
    InMemoryMembershipRepository,
    InMemoryWorkoutRepository,
    InMemoryBookingRepository
)

from src.service import FitnessClubService


def main():

    client_repo = InMemoryClientRepository()
    membership_repo = InMemoryMembershipRepository()
    workout_repo = InMemoryWorkoutRepository()
    booking_repo = InMemoryBookingRepository()

    service = FitnessClubService(
        client_repo,
        membership_repo,
        workout_repo,
        booking_repo
    )

    service.register_client(
        1,
        "Иван Петров",
        "ivan@example.com",
        "+79991234567"
    )

    service.buy_membership(
        1,
        1
    )

    service.create_workout(
        1,
        "CrossFit",
        "Алексей Иванов",
        10
    )

    service.book_workout(
        1,
        1
    )

    service.freeze_membership(
        1
    )

    print("Клиент зарегистрирован")
    print("Абонемент оформлен")
    print("Тренировка создана")
    print("Запись на тренировку выполнена")
    print("Абонемент заморожен")


if __name__ == "__main__":
=======
from src.memory_repositories import (
    InMemoryClientRepository,
    InMemoryMembershipRepository,
    InMemoryWorkoutRepository,
    InMemoryBookingRepository
)

from src.service import FitnessClubService


def main():

    client_repo = InMemoryClientRepository()
    membership_repo = InMemoryMembershipRepository()
    workout_repo = InMemoryWorkoutRepository()
    booking_repo = InMemoryBookingRepository()

    service = FitnessClubService(
        client_repo,
        membership_repo,
        workout_repo,
        booking_repo
    )

    service.register_client(
        1,
        "Иван Петров",
        "ivan@example.com",
        "+79991234567"
    )

    service.buy_membership(
        1,
        1
    )

    service.create_workout(
        1,
        "CrossFit",
        "Алексей Иванов",
        10
    )

    service.book_workout(
        1,
        1
    )

    service.freeze_membership(
        1
    )

    print("Клиент зарегистрирован")
    print("Абонемент оформлен")
    print("Тренировка создана")
    print("Запись на тренировку выполнена")
    print("Абонемент заморожен")


if __name__ == "__main__":
>>>>>>> 2f1db10bf35705f45bd43db49971fbda2ca12de9
    main()