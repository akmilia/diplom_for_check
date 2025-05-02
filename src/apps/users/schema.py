from pydantic import BaseModel 
from datetime import date, datetime, time #type: ignore
from typing import Literal, Optional #type: ignore 

# Авторизация
class LoginSchema(BaseModel):
    login: str
    password: str

class BearerSchema(BaseModel):
    # Основные поля для ответа
    access_token: str
    refresh_token: str
    token_type: Literal['bearer'] = 'bearer'
    
    # Данные пользователя
    user_id: int
    role: str
    
    # Время истечения (опционально, но рекомендуется)
    expires_in: Optional[int] = None #type: ignore
    expires_at: Optional[datetime] = None #type: ignore
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUz...",
                "refresh_token": "eyJhbGciOiJIUz...",
                "token_type": "bearer",
                "user_id": 1,
                "role": "Преподаватель",
                "expires_in":1800,
                "expires_at": "2025-05-01T12:00:00Z"
            }
        }
class ErrorResponse(BaseModel):
    detail: str
    status_code: int 

# Пользователи
class UserResponseSchema(BaseModel):
    idusers: int 
    full_name: str
    login: str 
    idroles: int

    class Config:
        from_attributes = True

class UserResponseSchemaBithdate(BaseModel):
    idusers: int 
    full_name: str
    login: str 
    birthdate: date
    id_roles: int
    user_role: str
    class Config:
        from_attributes = True 
# Предметы

class TypeSchema(BaseModel):
    id: int  
    type: str 
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "type": "Основной"
            }
        }
class SubjectSchema(BaseModel):
    subject_id: int
    subject_name: str
    description: str 
    types: list[TypeSchema]  # Используем TypeSchema
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "subject_id": 1,
                "subject_name": "Математика",
                "description": "Базовый курс",
                "types": [
                    {"id": 1, "type": "Основной"},
                    {"id": 2, "type": "Дополнительный"}
                ]
            }
        }
class GroupSchema(BaseModel): 
    idgroups: int
    name: str
    class Config:
        from_attributes = True  

# Расписание
class ScheduleTeacherSchema(BaseModel):
    full_name: str
    
    @classmethod
    def from_string(cls, teacher_str: str) -> 'ScheduleTeacherSchema':
        parts = teacher_str.split()
        if len(parts) >= 1:
            surname = parts[0]
            name = parts[1][0] + '.' if len(parts) > 1 else ''
            paternity = parts[2][0] + '.' if len(parts) > 2 else ''
            return cls(full_name=f"{surname} {name}{paternity}".strip())
        return cls(full_name=teacher_str)

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
    idschedule: int
    time: str  # Формат "HH:MM"
    subject_name: str
    teacher: ScheduleTeacherSchema
    cabinet: str
    group_name: Optional[str] #type: ignore
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

