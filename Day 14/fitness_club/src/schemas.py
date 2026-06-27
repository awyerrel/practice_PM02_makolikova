<<<<<<< HEAD
from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str


class WorkoutCreate(BaseModel):
    title: str
    trainer: str
=======
from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str


class WorkoutCreate(BaseModel):
    title: str
    trainer: str
>>>>>>> 2f1db10bf35705f45bd43db49971fbda2ca12de9
    max_participants: int = Field(gt=0)