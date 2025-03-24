from datetime import timedelta
from logging import getLogger
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from jwt import encode
from sqlmodel import col, select

from database import AsyncSessionDep

from .auth import ALGORITHM, SECRET_KEY, admin, user_auth
from .models import Cabinet, Role, Schedule, ScheduleCabinet, ScheduleSubject, Subject, User
from .schema import (
    BearerSchema,
    LoginSchema,
    ScheduleSchema,
    SchedulesSchema,
    SessionSchema,
    SubjectSchema,
    TeacherSchema,
    UserSchema,
)

logger = getLogger(__name__)

router = APIRouter()


@router.post('/login', response_model=BearerSchema)
async def login(session: AsyncSessionDep, login_data: LoginSchema):
    user = (
        await session.execute(
            select(User)
            .where(User.login == login_data.login)
            .where(User.password == login_data.password)
        )
    ).scalar_one_or_none()

    if not user or not user.id:
        raise HTTPException(status_code=404, detail='User not found')

    role = (await session.execute(select(Role).where(Role.id == user.role_id))).scalar_one()

    user_session = SessionSchema(role=role.name, user_id=user.id)
    encoded_jwt = str(encode(user_session.model_dump(), SECRET_KEY, algorithm=ALGORITHM))

    return BearerSchema(access_token=encoded_jwt, role=role.name)


@router.get('/profile', response_model=User, dependencies=[Depends(user_auth)])
async def get_profile(user: Annotated[User, Depends(user_auth)]):
    return user


@router.get('/users', response_model=list[User], dependencies=[Depends(admin)])
async def get_users(session: AsyncSessionDep):
    return (await session.execute(select(User))).scalars().all()


@router.post('/users', response_model=User, dependencies=[Depends(admin)])
async def create_user(session: AsyncSessionDep, user: UserSchema):
    u = User(
        surname=user.surname,
        name=user.name,
        paternity=user.paternity,
        gender=user.gender,
        birthdate=user.birthdate,
        login=user.login,
        password=user.password,
        role_id=user.role_id,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


@router.get('/teachers', response_model=list[User], dependencies=[Depends(admin)])
async def get_teachers(session: AsyncSessionDep):
    return (await session.execute(select(User).where(User.role_id == 2))).scalars().all()


@router.get('/subjects', response_model=list[Subject], dependencies=[Depends(admin)])
async def get_subjects(session: AsyncSessionDep):
    return (await session.execute(select(Subject))).scalars().all()


@router.post('/subjects', response_model=Subject, dependencies=[Depends(admin)])
async def create_subject(session: AsyncSessionDep, subject_schema: SubjectSchema):
    subject = Subject(
        name=subject_schema.name,
        description=subject_schema.description,
        type=subject_schema.type,
    )
    session.add(subject)
    await session.commit()
    await session.refresh(subject)
    return subject


@router.get('/schedule', response_model=list[SchedulesSchema], dependencies=[Depends(admin)])
async def get_schedule(session: AsyncSessionDep):
    schedules_stmt = (
        select(Schedule, Cabinet, Subject, User)
        .join(ScheduleCabinet, col(Schedule.id) == col(ScheduleCabinet.schedule_id))
        .join(ScheduleSubject, col(Schedule.id) == col(ScheduleSubject.schedule_id))
        .join(Cabinet, col(ScheduleCabinet.cabinet_id) == col(Cabinet.id))
        .join(Subject, col(ScheduleSubject.subject_id) == col(Subject.id))
        .join(User, col(Schedule.teacher_id) == col(User.id))
        .where(User.role_id == 2)
        .order_by(col(Schedule.dateandtime).asc())
    )
    schedules = (await session.execute(schedules_stmt)).all()
    schedules_list: list[SchedulesSchema] = []

    schedule: Schedule
    cabinet: Cabinet
    subject: Subject
    teacher: User

    for schedule, cabinet, subject, teacher in schedules:
        if subject.type not in ('sport', 'art', 'free', 'paid'):
            raise HTTPException(status_code=400, detail='Invalid subject type')

        sch = ScheduleSchema(
            cabinet=cabinet.description,
            date_n_time=schedule.dateandtime,
            subject=SubjectSchema(
                id=subject.id,
                name=subject.name,
                description=subject.description,
                type=subject.type,
            ),
            teacher=TeacherSchema(
                name=teacher.name,
                surname=teacher.surname,
                paternity=teacher.paternity,
            ),
        )

        is_added = False
        for s in schedules_list:
            if s.date == schedule.dateandtime.date():
                s.schedules.append(sch)
                is_added = True
                break

        if not is_added:
            schedules_list.append(
                SchedulesSchema(
                    date=schedule.dateandtime.date(),
                    day_name=schedule.dateandtime.strftime('%A'),
                    schedules=[sch],
                )
            )

    return schedules_list


@router.post('/schedule', response_model=list[ScheduleSchema], dependencies=[Depends(admin)])
async def create_schedule(session: AsyncSessionDep, schedule_data: ScheduleSchema):
    cabinet_stmt = select(Cabinet).where(Cabinet.description == schedule_data.cabinet)
    cabinet = (await session.execute(cabinet_stmt)).scalar_one_or_none()

    if not cabinet or not cabinet.id:
        cabinet = Cabinet(description=schedule_data.cabinet)
        session.add(cabinet)

    subject_stmt = select(Subject).where(Subject.name == schedule_data.subject.name)
    subject = (await session.execute(subject_stmt)).scalar_one_or_none()

    if not subject or not subject.id:
        subject = Subject(
            name=schedule_data.subject.name,
            description=schedule_data.subject.description,
            type=schedule_data.subject.type,
        )
        session.add(subject)

    teacher_stmt = (
        select(User)
        .join(Role)
        .where(Role.name == 'teacher')
        .where(Role.id == User.role_id)
        .where(User.name == schedule_data.teacher.name)
        .where(User.surname == schedule_data.teacher.surname)
        .where(User.paternity == schedule_data.teacher.paternity)
    )
    teacher = (await session.execute(teacher_stmt)).scalar_one_or_none()

    if not teacher or not teacher.id:
        raise HTTPException(status_code=404, detail='Teacher not found')

    dates = [schedule_data.date_n_time + timedelta(weeks=i) for i in range(15)]
    schedules: list[ScheduleSchema] = []

    for date in dates:
        schedule = Schedule(
            dateandtime=date,
            teacher_id=teacher.id,
        )

        session.add(schedule)
        await session.commit()

        await session.refresh(cabinet)
        await session.refresh(subject)
        await session.refresh(teacher)
        await session.refresh(schedule)

        if not schedule.id or not cabinet.id or not subject.id or not teacher.id:
            raise HTTPException(status_code=500, detail='Internal Server Error')

        s = ScheduleSubject(schedule_id=schedule.id, subject_id=subject.id)
        c = ScheduleCabinet(schedule_id=schedule.id, cabinet_id=cabinet.id)

        session.add(s)
        session.add(c)
        await session.commit()

        await session.refresh(cabinet)
        await session.refresh(subject)
        await session.refresh(teacher)
        await session.refresh(schedule)

        schedules.append(
            ScheduleSchema(
                cabinet=cabinet.description,
                date_n_time=schedule.dateandtime,
                subject=SubjectSchema(
                    id=subject.id,
                    name=subject.name,
                    description=subject.description,
                    type=schedule_data.subject.type,
                ),
                teacher=TeacherSchema(
                    name=teacher.name,
                    surname=teacher.surname,
                    paternity=teacher.paternity,
                ),
            )
        )

    return schedules
