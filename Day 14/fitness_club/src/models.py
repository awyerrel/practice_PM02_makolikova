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
    workout_id: int