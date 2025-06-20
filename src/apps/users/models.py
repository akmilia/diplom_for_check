from typing import List, Optional # type: ignore
from sqlalchemy import Boolean, Column, JSON,  Date, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, Table, Text, Time, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

import datetime

class Base(DeclarativeBase):
    pass
class Cabinets(Base):
    __tablename__ = 'cabinets'
    __table_args__ = (
        PrimaryKeyConstraint('idcabinet', name='cabinets_pkey'),
    )

    idcabinet: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(45)) # type: ignore

    schedule: Mapped[List['Schedule']] = relationship('Schedule', back_populates='cabinets') # type: ignore


class Groups(Base):
    __tablename__ = 'groups'
    __table_args__ = (
        PrimaryKeyConstraint('idgroups', name='groups_pkey'),
    )

    idgroups: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(45)) # type: ignore

    users: Mapped[List['Users']] = relationship('Users', secondary='groups_users', back_populates='groups') # type: ignore
    schedule: Mapped[List['Schedule']] = relationship('Schedule', back_populates='groups') # type: ignore


class Roles(Base):
    __tablename__ = 'roles'
    __table_args__ = (
        PrimaryKeyConstraint('idroles', name='roles_pkey'),
    )

    idroles: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(25)) # type: ignore

    users: Mapped[List['Users']] = relationship('Users', back_populates='roles') # type: ignore


t_scheduleshow = Table(
    'scheduleshow', Base.metadata,
    Column('idschedule', Integer),
    Column('time', Time(True)),
    Column('subject_name', String(45)),
    Column('teacher', String(45)),
    Column('cabinet', Integer),
    Column('group_nam', String(45)),
    Column('day_of_week', Text)
) 

t_scheduleshow_extra = Table(
    'scheduleshow_extra', Base.metadata,
    Column('idschedule', Integer),
    Column('time', Time(True)),
    Column('subject_name', String(45)), 
    Column('teacher', String(45)),
    Column('teacher_id', Integer),
    Column('cabinet', Integer), 
    Column('group_id', Integer),
    Column('group_nam', String(45)),
    Column('day_of_week', Text)
)


class Subjects(Base):
    __tablename__ = 'subjects'
    __table_args__ = (
        PrimaryKeyConstraint('idsubjects', name='subjects_pkey'),
    )

    idsubjects: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(45))
    description: Mapped[Optional[str]] = mapped_column(String(150)) # type: ignore

    types: Mapped[List['Types']] = relationship('Types', secondary='types_subjects', back_populates='subjects') # type: ignore
    schedule: Mapped[List['Schedule']] = relationship('Schedule', back_populates='subjects') # type: ignore


t_subjectsshow = Table(
    'subjectsshow', Base.metadata,
    Column('subject_id', Integer),
    Column('subject_name', String(45)),
    Column('description', String(150)),
    Column('type_id', Integer),
    Column('type_name', String(45))
)

t_subjects_with_types = Table(
    'subjects_with_types', 
    Base.metadata,
    Column('subject_id', Integer, primary_key=True),
    Column('subject_name', String(45)),
    Column('description', String(150)),
    Column('types', JSON)  # Для хранения JSON-массива типов
)

class Types(Base):
    __tablename__ = 'types'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='types_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[Optional[str]] = mapped_column(String(45)) # type: ignore

    subjects: Mapped[List['Subjects']] = relationship('Subjects', secondary='types_subjects', back_populates='types') # type: ignore


t_usersshow = Table(
    'usersshow', Base.metadata,
    Column('idusers', Integer),
    Column('login', String(25)),
    Column('password', String(25)),
    Column('full_name', Text),
    Column('idroles', Integer),
    Column('user_role', String(25))
)

t_usersshow_with_birthdate = Table(
    'usersshow_with_birthdate', Base.metadata,
    Column('idusers', Integer),
    Column('login', String(250)),
    Column('birthdate', Date),
    Column('full_name', Text),
    Column('idroles', Integer),
    Column('user_role', String(25)),
    schema='public'
) 

class TypesSubjects(Base):
    __tablename__ = 'types_subjects'
    __table_args__ = (
        ForeignKeyConstraint(
            ['subjects_idsubjects'],
            ['subjects.idsubjects'],
            ondelete='CASCADE',
            name='idsubject_fkey'
        ),
        ForeignKeyConstraint(
            ['types_id'],
            ['types.id'],
            name='types_subjects_types_id_fkey'
        ),
        PrimaryKeyConstraint('types_id', 'subjects_idsubjects', name='types_subjects_pkey')
    )
    
    types_id = Column(Integer, nullable=False)
    subjects_idsubjects = Column(Integer, nullable=False)

class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        ForeignKeyConstraint(['roles_idroles'], ['roles.idroles'], name='users_roles_idroles_fkey'),
        PrimaryKeyConstraint('idusers', name='users_pkey'),
        UniqueConstraint('idusers', name='users_idusers_key'),
        UniqueConstraint('login', name='users_login_key')
    )

    idusers: Mapped[int] = mapped_column(Integer, primary_key=True)
    surname: Mapped[str] = mapped_column(String(45))
    name: Mapped[str] = mapped_column(String(45))
    login: Mapped[str] = mapped_column(String(25))
    roles_idroles: Mapped[int] = mapped_column(Integer)
    paternity: Mapped[Optional[str]] = mapped_column(String(45)) # type: ignore
    birthdate: Mapped[Optional[datetime.date]] = mapped_column(Date) # type: ignore
    password: Mapped[Optional[str]] = mapped_column(String(25)) # type: ignore

    groups: Mapped[List['Groups']] = relationship('Groups', secondary='groups_users', back_populates='users') # type: ignore
    roles: Mapped['Roles'] = relationship('Roles', back_populates='users')
    schedule: Mapped[List['Schedule']] = relationship('Schedule', back_populates='users') # type: ignore

 
class GroupsUsers(Base):
    __tablename__ = 'groups_users'
    __table_args__ = (
        ForeignKeyConstraint(
            ['groups_idgroups'],
            ['groups.idgroups'],
            name='groups_users_groups_idgroups_fkey'
        ),
        ForeignKeyConstraint(
            ['users_idusers'],
            ['users.idusers'],
            name='groups_users_users_idusers_fkey'
        ),
        PrimaryKeyConstraint('groups_idgroups', 'users_idusers', name='groups_users_pkey')
    )
    
    groups_idgroups = Column(Integer, nullable=False)
    users_idusers = Column(Integer, nullable=False)

class Schedule(Base):
    __tablename__ = 'schedule'
    __table_args__ = (
        ForeignKeyConstraint(['cabinets_idcabinet'], ['cabinets.idcabinet'], name='schedule_cabinets_idcabinet_fkey'),
        ForeignKeyConstraint(['groups_idgroup'], ['groups.idgroups'], name='schedule_group_idgroup_fkey'),
        ForeignKeyConstraint(['subjects_idsubjects'], ['subjects.idsubjects'], name='schedule_subjects_idsubjects_fkey'),
        ForeignKeyConstraint(['users_idusers'], ['users.idusers'], name='schedule_users_idusers_fkey'),
        PrimaryKeyConstraint('idschedule', name='schedule_pk')
    )

    idschedule: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[datetime.time] = mapped_column(Time(True))
    subjects_idsubjects: Mapped[int] = mapped_column(Integer)
    users_idusers: Mapped[int] = mapped_column(Integer)
    cabinets_idcabinet: Mapped[int] = mapped_column(Integer)
    day_of_week: Mapped[int] = mapped_column(Integer)
    groups_idgroup: Mapped[Optional[int]] = mapped_column(Integer) # type: ignore

    cabinets: Mapped['Cabinets'] = relationship('Cabinets', back_populates='schedule')
    groups: Mapped[Optional['Groups']] = relationship('Groups', back_populates='schedule')# type: ignore
    subjects: Mapped['Subjects'] = relationship('Subjects', back_populates='schedule')
    users: Mapped['Users'] = relationship('Users', back_populates='schedule')
    attendance: Mapped[List['Attendance']] = relationship('Attendance', back_populates='schedule') # type: ignore


class Attendance(Base):
    __tablename__ = 'attendance'
    __table_args__ = (
        ForeignKeyConstraint(['idschedule'], ['schedule.idschedule'], name='attendance_schedule_idschedule'),
        PrimaryKeyConstraint('idattendance', name='attendance_pkey')
    )

    idattendance: Mapped[int] = mapped_column(Integer, primary_key=True)
    idschedule: Mapped[int] = mapped_column(Integer)
    date: Mapped[datetime.date] = mapped_column(Date)

    schedule: Mapped['Schedule'] = relationship('Schedule', back_populates='attendance')
    bil_nebil: Mapped[List['BilNebil']] = relationship('BilNebil', back_populates='attendance') # type: ignore


class BilNebil(Base):
    __tablename__ = 'bil_nebil'
    __table_args__ = (
        ForeignKeyConstraint(['idattendance'], ['attendance.idattendance'], name='bil_attendance_idattendance'),
        PrimaryKeyConstraint('idattendance', 'iduser', name='bil_nebil_pkey')
    )

    idattendance: Mapped[int] = mapped_column(Integer, primary_key=True)
    iduser: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[Optional[bool]] = mapped_column(Boolean)  # type: ignore

    attendance: Mapped['Attendance'] = relationship('Attendance', back_populates='bil_nebil')
