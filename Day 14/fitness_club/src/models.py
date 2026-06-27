<<<<<<< HEAD
from dataclasses import dataclass
from datetime import date


@dataclass
class Client:
    id: int
    name: str
    email: str
    phone: str


@dataclass
class Membership:
    id: int
    client_id: int
    start_date: date
    end_date: date
    frozen: bool = False


@dataclass
class Workout:
    id: int
    title: str
    trainer: str
    max_participants: int


@dataclass
class Booking:
    client_id: int
=======
from dataclasses import dataclass
from datetime import date


@dataclass
class Client:
    id: int
    name: str
    email: str
    phone: str


@dataclass
class Membership:
    id: int
    client_id: int
    start_date: date
    end_date: date
    frozen: bool = False


@dataclass
class Workout:
    id: int
    title: str
    trainer: str
    max_participants: int


@dataclass
class Booking:
    client_id: int
>>>>>>> 2f1db10bf35705f45bd43db49971fbda2ca12de9
    workout_id: int