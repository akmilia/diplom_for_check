from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, PositiveInt


class SessionSchema(BaseModel):
    role: str
    user_id: int


class LoginSchema(BaseModel):
    login: str
    password: str


class BearerSchema(BaseModel):
    access_token: str
    role: str
    token_type: Literal['bearer'] = 'bearer'

class UserSchema(BaseModel):
    role_id: int
    name: str
    surname: str
    gender: str
    paternity: str | None = None
    birthdate: datetime | None = None
    login: str
    password: str

class SubjectSchema(BaseModel):
    id: PositiveInt | None
    name: str
    description: str
    type: Literal['sport', 'art', 'free', 'paid']


class TeacherSchema(BaseModel):
    name: str
    surname: str
    paternity: str | None


class ScheduleSchema(BaseModel):
    date_n_time: datetime
    cabinet: str
    subject: SubjectSchema
    teacher: TeacherSchema


class SchedulesSchema(BaseModel):
    date: date
    day_name: str
    schedules: list[ScheduleSchema]
