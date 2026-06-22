from pydantic import BaseModel, EmailStr, Field


class ClientCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str


class WorkoutCreate(BaseModel):
    title: str
    trainer: str
    max_participants: int = Field(gt=0)