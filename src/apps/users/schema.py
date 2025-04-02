from pydantic import BaseModel 
from pydantic import computed_field
from datetime import date, datetime, time #type: ignore
from typing import Literal, Optional #type: ignore 

# Авторизация
class LoginSchema(BaseModel):
    login: str
    password: str

class BearerSchema(BaseModel):
    access_token: str
    role: str  # Например, "admin", "teacher", "student"
    token_type: Literal['bearer'] = 'bearer'

# Пользователи
class UserCreateSchema(BaseModel):
    name: str
    surname: str
    paternity: Optional[str] = None #type: ignore
    birthdate: Optional[date] = None #type: ignore
    login: str
    password: str
    role_id: int  # Ссылка на roles.idroles

class UserResponseSchema(BaseModel):
    id: int
    name: str
    surname: str
    paternity: Optional[str] = None #type: ignore
    login: str
    role: str  # Название роли (например, "Администратор")

    class Config:
        from_attributes = True

# Предметы
class SubjectTypeSchema(BaseModel):
    id: int
    type: str  # "sport", "art", "education"

    class Config:
        from_attributes = True

class SubjectSchema(BaseModel):
    id: int
    name: str
    description: str
    types: list[SubjectTypeSchema]  # Список типов предмета

    class Config:
        from_attributes = True  

class SubjectCreateSchema(BaseModel): 
    name: str
    description: str
    type_ids: list[int]  # Список типов предмета

    class Config:
        from_attributes = True  

# Расписание
class ScheduleTeacherSchema(BaseModel):
    id: int
    surname: str
    name: str
    paternity: Optional[str] = None #type: ignore
    
    @computed_field
    @property
    def full_name(self) -> str:
        initials: list[str] = []  # Явная аннотация типа
        if self.name:
            initials.append(f"{self.name[0]}.")
        if self.paternity:
            initials.append(f"{self.paternity[0]}.")
        
        return f"{self.surname} {' '.join(initials)}".strip()
    
    class Config:
        from_attributes = True

class ScheduleSubjectSchema(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class ScheduleGroupSchema(BaseModel):
    id: int
    group_name: str
    class Config:
        from_attributes = True

class ScheduleEntrySchema(BaseModel):
    id: int
    time: time  # Время занятия (например, "15:15:00")
    subject: ScheduleSubjectSchema
    teacher: ScheduleTeacherSchema
    cabinet: str  # Название кабинета
    group_name: ScheduleGroupSchema
    day_of_week: str  
    class Config:
        from_attributes = True

class ScheduleEntryResponse(BaseModel):
    idschedule: int
    time: str  # Формат "HH:MM"
    subject_name: str
    teacher: ScheduleTeacherSchema
    cabinet: str
    group_name: Optional[str]  #type: ignore
    day_of_week: str
    dates: list[str]  # Даты в формате "dd.MM.yyyy"
    
    class Config:
        from_attributes = True

class DayScheduleSchema(BaseModel):
    date: date  # Конкретная дата (для посещаемости)
    day_name: str  # Название дня недели
    schedules: list[ScheduleEntrySchema]

# class SessionSchema(BaseModel):
#     role: str
#     user_id: int


# class LoginSchema(BaseModel):
#     login: str
#     password: str


# class BearerSchema(BaseModel):
#     access_token: str
#     role: str
#     token_type: Literal['bearer'] = 'bearer'

# class UserSchema(BaseModel):
#     role_id: int
#     name: str
#     surname: str
#     gender: str
#     paternity: str | None = None
#     birthdate: datetime | None = None
#     login: str
#     password: str

# class SubjectSchema(BaseModel):
#     id: PositiveInt | None
#     name: str
#     description: str
#     type: Literal['sport', 'art', 'free', 'paid']


# class TeacherSchema(BaseModel):
#     name: str
#     surname: str
#     paternity: str | None


# class ScheduleSchema(BaseModel):
#     date_n_time: datetime
#     cabinet: str
#     subject: SubjectSchema
#     teacher: TeacherSchema


# class SchedulesSchema(BaseModel):
#     date: date
#     day_name: str
#     schedules: list[ScheduleSchema]
