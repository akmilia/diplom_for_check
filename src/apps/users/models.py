from typing import List # type: ignore

from fastapi import FastAPI
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Time, Boolean 
from sqlalchemy.orm import relationship 
from sqlalchemy.ext.declarative import declarative_base 

app = FastAPI()


Base = declarative_base()

class Attendance(Base):
    __tablename__ = "attendance"

    idattendance = Column(Integer, primary_key=True, autoincrement=True)
    idschedule = Column(Integer, ForeignKey("schedule.idschedule"), nullable=False)
    date = Column(Date, nullable=False)

    schedule = relationship("Schedule", back_populates="attendances")


class BilNebil(Base):
    __tablename__ = "bil_nebil"

    idattendance = Column(Integer, ForeignKey("attendance.idattendance"), primary_key=True)
    iduser = Column(Integer, ForeignKey("users.idusers"), primary_key=True)
    status = Column(Boolean)

    attendance = relationship("Attendance")
    user = relationship("Users")


class Cabinets(Base):
    __tablename__ = "cabinets"

    idcabinet = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(45))

    schedule_items = relationship("Schedule", back_populates="cabinet")


class Groups(Base):
    __tablename__ = "groups"

    idgroups = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45))

    schedule_items = relationship("Schedule", back_populates="group")
    users = relationship("Users", secondary="groups_users", back_populates="groups")


class GroupsUsers(Base):
    __tablename__ = "groups_users"

    groups_idgroups = Column(Integer, ForeignKey("groups.idgroups"), primary_key=True)
    users_idusers = Column(Integer, ForeignKey("users.idusers"), primary_key=True)


class Roles(Base):
    __tablename__ = "roles"

    idroles = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(25), unique=True)

    users = relationship("Users", back_populates="role")


class Schedule(Base):
    __tablename__ = "schedule"

    idschedule = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(Time(timezone=True), nullable=False)
    subjects_idsubjects = Column(Integer, ForeignKey("subjects.idsubjects"), nullable=False)
    users_idusers = Column(Integer, ForeignKey("users.idusers"), nullable=False)
    cabinets_idcabinet = Column(Integer, ForeignKey("cabinets.idcabinet"), nullable=False)
    groups_idgroup = Column(Integer, ForeignKey("groups.idgroups"))
    day_of_week = Column(Integer, nullable=False)

    subject = relationship("Subjects", back_populates="schedule_items")
    teacher = relationship("Users", back_populates="schedule_items")
    cabinet = relationship("Cabinets", back_populates="schedule_items")
    group = relationship("Groups", back_populates="schedule_items")
    attendances = relationship("Attendance", back_populates="schedule")


class Subjects(Base):
    __tablename__ = "subjects"

    idsubjects = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(45), nullable=False)
    description = Column(String(150))

    schedule_items = relationship("Schedule", back_populates="subject")
    types = relationship("Types", secondary="types_subjects", back_populates="subjects")


class Types(Base):
    __tablename__ = "types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(45))

    subjects = relationship("Subjects", secondary="types_subjects", back_populates="types")


class TypesSubjects(Base):
    __tablename__ = "types_subjects"

    types_id = Column(Integer, ForeignKey("types.id"), primary_key=True)
    subjects_idsubjects = Column(Integer, ForeignKey("subjects.idsubjects"), primary_key=True)


class Users(Base):
    __tablename__ = "users"

    idusers = Column(Integer, primary_key=True, autoincrement=True)
    surname = Column(String(45), nullable=False)
    name = Column(String(45), nullable=False)
    paternity = Column(String(45))
    birthdate = Column(Date)
    login = Column(String(25), unique=True, nullable=False)
    password = Column(String(25))
    roles_idroles = Column(Integer, ForeignKey("roles.idroles"), nullable=False)

    role = relationship("Roles", back_populates="users")
    schedule_items = relationship("Schedule", back_populates="teacher")
    groups = relationship("Groups", secondary="groups_users", back_populates="users")



# class User(SQLModel, table=True):
#     __tablename__ = 'user'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     surname: str = Field(max_length=45)
#     name: str = Field(max_length=45)
#     paternity: str | None = Field(max_length=45)
#     gender: str | None = Field(max_length=45)
#     birthdate: datetime | None = Field(default=None)
#     login: str = Field(max_length=25, unique=True)
#     password: str = Field(max_length=25)
#     role_id: int = Field(foreign_key='role.id')


# class Role(SQLModel, table=True):
#     __tablename__ = 'role'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     name: str = Field(max_length=25)


# class Group(SQLModel, table=True):
#     __tablename__ = 'group'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     name: str = Field(max_length=25)


# class UserGroup(SQLModel, table=True):
#     __tablename__ = 'user_group'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     user_id: int = Field(foreign_key='user.id')
#     group_id: int = Field(foreign_key='group.id')


# class Cabinet(SQLModel, table=True):
#     __tablename__ = 'cabinet'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     description: str = Field(max_length=45)


# class Subject(SQLModel, table=True):
#     __tablename__ = 'subject'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     name: str = Field(max_length=50)
#     description: str = Field(max_length=50)
#     type: str = Field(max_length=50)


# class Schedule(SQLModel, table=True):
#     __tablename__ = 'schedule'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     dateandtime: datetime = Field(default_factory=datetime.now)
#     teacher_id: int = Field(foreign_key='user.id')


# class ScheduleSubject(SQLModel, table=True):
#     __tablename__ = 'schedule_subject'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     schedule_id: int = Field(foreign_key='schedule.id')
#     subject_id: int = Field(foreign_key='subject.id')


# class ScheduleCabinet(SQLModel, table=True):
#     __tablename__ = 'schedule_cabinet'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     schedule_id: int = Field(foreign_key='schedule.id')
#     cabinet_id: int = Field(foreign_key='cabinet.id')


# from datetime import datetime

# from sqlmodel import Field, SQLModel


# class User(SQLModel, table=True):
#     __tablename__ = 'user'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     surname: str = Field(max_length=45)
#     name: str = Field(max_length=45)
#     paternity: str | None = Field(max_length=45)
#     gender: str | None = Field(max_length=45)
#     birthdate: datetime | None = Field(default=None)
#     login: str = Field(max_length=25, unique=True)
#     password: str = Field(max_length=25)
#     role_id: int = Field(foreign_key='role.id')


# class Role(SQLModel, table=True):
#     __tablename__ = 'role'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     name: str = Field(max_length=25)


# class Group(SQLModel, table=True):
#     __tablename__ = 'group'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     name: str = Field(max_length=25)


# class UserGroup(SQLModel, table=True):
#     __tablename__ = 'user_group'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     user_id: int = Field(foreign_key='user.id')
#     group_id: int = Field(foreign_key='group.id')


# class Cabinet(SQLModel, table=True):
#     __tablename__ = 'cabinet'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     description: str = Field(max_length=45)


# class Subject(SQLModel, table=True):
#     __tablename__ = 'subject'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     name: str = Field(max_length=50)
#     description: str = Field(max_length=50)
#     type: str = Field(max_length=50)


# class Schedule(SQLModel, table=True):
#     __tablename__ = 'schedule'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     dateandtime: datetime = Field(default_factory=datetime.now)
#     teacher_id: int = Field(foreign_key='user.id')


# class ScheduleSubject(SQLModel, table=True):
#     __tablename__ = 'schedule_subject'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     schedule_id: int = Field(foreign_key='schedule.id')
#     subject_id: int = Field(foreign_key='subject.id')


# class ScheduleCabinet(SQLModel, table=True):
#     __tablename__ = 'schedule_cabinet'  # type: ignore

#     id: int | None = Field(default=None, primary_key=True, unique=True)
#     schedule_id: int = Field(foreign_key='schedule.id')
#     cabinet_id: int = Field(foreign_key='cabinet.id')
