<<<<<<< HEAD
import logging
from datetime import date, timedelta

from src.models import (
    Client,
    Membership,
    Workout,
    Booking
)

from src.exceptions import (
    ClientNotFound,
    MembershipExpired,
    MembershipFrozen,
    WorkoutFull,
    MembershipNotFound
)

logging.basicConfig(
    filename="fitness.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


class FitnessClubService:

    def __init__(
            self,
            client_repo,
            membership_repo,
            workout_repo,
            booking_repo):

        self.client_repo = client_repo
        self.membership_repo = membership_repo
        self.workout_repo = workout_repo
        self.booking_repo = booking_repo

    def register_client(self, client_id, name, email, phone):

        client = Client(
            id=client_id,
            name=name,
            email=email,
            phone=phone
        )

        self.client_repo.add(client)

        logging.info(f"Клиент зарегистрирован: {name}")

        return client

    def buy_membership(self, membership_id, client_id):

        membership = Membership(
            id=membership_id,
            client_id=client_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )

        self.membership_repo.add(membership)

        logging.info(f"Абонемент оформлен клиенту {client_id}")

        return membership

    def freeze_membership(self, client_id):

        membership = self.membership_repo.get_active(client_id)

        if not membership:
            logging.warning(f"Абонемент для клиента {client_id} не найден")
            raise MembershipNotFound()

        membership.frozen = True
        logging.info(f"Абонемент клиента {client_id} заморожен")

    def create_workout(self, workout_id, title, trainer, max_participants):

        workout = Workout(
            id=workout_id,
            title=title,
            trainer=trainer,
            max_participants=max_participants
        )

        self.workout_repo.add(workout)

        logging.info(f"Создана тренировка {title}")

        return workout

    def book_workout(self, client_id, workout_id):

        client = self.client_repo.get_by_id(client_id)

        if not client:
            raise ClientNotFound()

        membership = self.membership_repo.get_active(client_id)

        if not membership or membership.end_date < date.today():
            raise MembershipExpired()

        if membership.frozen:
            raise MembershipFrozen()

        workout = self.workout_repo.get_by_id(workout_id)

        participants = self.booking_repo.count_for_workout(workout_id)

        if participants >= workout.max_participants:
            raise WorkoutFull()

        booking = Booking(
            client_id=client_id,
            workout_id=workout_id
        )

        self.booking_repo.add(booking)

        logging.info(f"Клиент {client_id} записан на тренировку {workout_id}")

        return booking

    def attendance(self, client_id):

        logging.info(f"Посещение отмечено для клиента {client_id}")

    def calculate_discount(self, visits_count):

        if visits_count > 20:
            return 15

=======
import logging
from datetime import date, timedelta

from src.models import (
    Client,
    Membership,
    Workout,
    Booking
)

from src.exceptions import (
    ClientNotFound,
    MembershipExpired,
    MembershipFrozen,
    WorkoutFull,
    MembershipNotFound
)

logging.basicConfig(
    filename="fitness.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)


class FitnessClubService:

    def __init__(
            self,
            client_repo,
            membership_repo,
            workout_repo,
            booking_repo):

        self.client_repo = client_repo
        self.membership_repo = membership_repo
        self.workout_repo = workout_repo
        self.booking_repo = booking_repo

    def register_client(self, client_id, name, email, phone):

        client = Client(
            id=client_id,
            name=name,
            email=email,
            phone=phone
        )

        self.client_repo.add(client)

        logging.info(f"Клиент зарегистрирован: {name}")

        return client

    def buy_membership(self, membership_id, client_id):

        membership = Membership(
            id=membership_id,
            client_id=client_id,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )

        self.membership_repo.add(membership)

        logging.info(f"Абонемент оформлен клиенту {client_id}")

        return membership

    def freeze_membership(self, client_id):

        membership = self.membership_repo.get_active(client_id)

        if not membership:
            logging.warning(f"Абонемент для клиента {client_id} не найден")
            raise MembershipNotFound()

        membership.frozen = True
        logging.info(f"Абонемент клиента {client_id} заморожен")

    def create_workout(self, workout_id, title, trainer, max_participants):

        workout = Workout(
            id=workout_id,
            title=title,
            trainer=trainer,
            max_participants=max_participants
        )

        self.workout_repo.add(workout)

        logging.info(f"Создана тренировка {title}")

        return workout

    def book_workout(self, client_id, workout_id):

        client = self.client_repo.get_by_id(client_id)

        if not client:
            raise ClientNotFound()

        membership = self.membership_repo.get_active(client_id)

        if not membership or membership.end_date < date.today():
            raise MembershipExpired()

        if membership.frozen:
            raise MembershipFrozen()

        workout = self.workout_repo.get_by_id(workout_id)

        participants = self.booking_repo.count_for_workout(workout_id)

        if participants >= workout.max_participants:
            raise WorkoutFull()

        booking = Booking(
            client_id=client_id,
            workout_id=workout_id
        )

        self.booking_repo.add(booking)

        logging.info(f"Клиент {client_id} записан на тренировку {workout_id}")

        return booking

    def attendance(self, client_id):

        logging.info(f"Посещение отмечено для клиента {client_id}")

    def calculate_discount(self, visits_count):

        if visits_count > 20:
            return 15

>>>>>>> 2f1db10bf35705f45bd43db49971fbda2ca12de9
        return 5