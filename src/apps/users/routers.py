from datetime import date, datetime, time, timedelta
from typing import Annotated, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, join, and_
from sqlalchemy.orm import Session, selectinload, joinedload

from apps.users.models import (
    Users, Roles, Groups, Types, Schedule, Attendance, Subjects, TypesSubjects,
    BilNebil, Cabinets, t_types_subjects, t_groups_users, t_subjectsshow
)
from apps.users.schema import (
    BearerSchema, LoginSchema, UserResponseSchema, ScheduleTeacherSchema, 
    SubjectSchema, ScheduleEntryResponse, DayScheduleSchema, UserCreateSchema
)
from database.manager import AsyncSession
from  middlewares.security import encode, SECRET_KEY, ALGORITHM

router = APIRouter
#просто авторизация по входным данным 

@router.post('/login', response_model=BearerSchema)
async def login(
    session: AsyncSession,
    login_data: LoginSchema
):
    # Ищем пользователя по логину и паролю
    user = (await session.execute(
        select(Users)
        .where(Users.login == login_data.login)
        .where(Users.password == login_data.password)
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    # Получаем роль пользователя
    role = (await session.execute(
        select(Roles).where(Roles.idroles == user.roles_idroles)
    )).scalar_one()

    # Генерируем токен (ваша текущая реализация)
    encoded_jwt = str(encode(
        {"role": role.name, "user_id": user.idusers},
        SECRET_KEY,
        algorithm=ALGORITHM
    ))

    return BearerSchema(
        access_token=encoded_jwt,
        role=role.name
    ) 

# @router.post('/login', response_model=BearerSchema)
# async def login(session: AsyncSessionDep, login_data: LoginSchema):
#     user = (
#         await session.execute(
#             select(User)
#             .where(User.login == login_data.login)
#             .where(User.password == login_data.password)
#         )
#     ).scalar_one_or_none()

#     if not user or not user.id:
#         raise HTTPException(status_code=404, detail='User not found')

#     role = (await session.execute(select(Role).where(Role.id == user.role_id))).scalar_one()

#     user_session = SessionSchema(role=role.name, user_id=user.id)
#     encoded_jwt = str(encode(user_session.model_dump(), SECRET_KEY, algorithm=ALGORITHM))

#     return BearerSchema(access_token=encoded_jwt, role=role.name)


# @router.get('/profile', response_model=Users, dependencies=[Depends(user_auth)])
# async def get_profile(user: Annotated[User, Depends(user_auth)]):
#     return user


@router.get('/users', response_model=list[Users], dependencies=[Depends(admin)])
async def get_users(session: AsyncSession):
    return (await session.execute(select(Users))).scalars().all()


@router.post('/users', response_model=Users, dependencies=[Depends(admin)])
async def create_user(session: AsyncSession, user: UserCreateSchema):
    u = Users(
        surname=user.surname,
        name=user.name,
        paternity=user.paternity,
        birthdate=user.birthdate,
        login=user.login,
        password=user.password,
        role_id=user.role_id,
    )
    session.add(u)
    await session.commit()
    await session.refresh(u)
    return u


@router.get('/teachers', response_model=list[Users], dependencies=[Depends(admin)])
async def get_teachers(session: AsyncSession):
    return (await session.execute(select(Users).where(Users.roles_idroles == 2))).scalars().all()


# @router.get('/subjects', response_model=list[Subject], dependencies=[Depends(admin)])
# async def get_subjects(session: AsyncSessionDep):
#     return (await session.execute(select(Subject))).scalars().all()


# @router.post('/subjects', response_model=Subject, dependencies=[Depends(admin)])
# async def create_subject(session: AsyncSessionDep, subject_schema: SubjectSchema):
#     subject = Subject(
#         name=subject_schema.name,
#         description=subject_schema.description,
#         type=subject_schema.type,
#     )
#     session.add(subject)
#     await session.commit()
#     await session.refresh(subject)
#     return subject 

@router.get('/subjects', response_model=list[SubjectSchema])
async def get_subjects(
    session: AsyncSession
):
    # Получаем все предметы из представления
    subjects = (await session.execute(
        select(t_subjectsshow)
    )).scalars().all()
    
    if not subjects:
        raise HTTPException(status_code=404, detail='Предметы не найдены')
    
    return subjects

#очень интересно, но нафиг оно надо - это админка, которой тут нет
# @router.post('/subjects', response_model=SubjectSchema, dependencies=[Depends(admin)])
# async def create_subject(
#     session: AsyncSession,
#     subject_data: SubjectCreateSchema
# ):
#     # Создаем новый предмет
#     new_subject = Subjects(
#         name=subject_data.name,
#         description=subject_data.description
#     )
#     session.add(new_subject)
#     await session.commit()
#     await session.refresh(new_subject)
    
#     # Создаем связь с типом
#     for type_id in subject_data.type_ids:
#         type_subject = TypesSubjects(
#             types_id=type_id,
#             subjects_idsubjects=new_subject.idsubjects
#         )
#         session.add(type_subject)
    
#     await session.commit()
   
#     # Получаем созданный предмет из представления
#     created_subject = (await session.execute(
#         select(SubjectSchema)
#         .where(SubjectSchema.id == new_subject.idsubjects)
#     )).scalar_one_or_none()
    
#     if not created_subject:
#         raise HTTPException(status_code=500, detail='Ошибка при создании предмета')
  
#     return created_subject

@router.get('/schedule', response_model=list[ScheduleEntryResponse])
async def get_schedule(
    session: AsyncSession,
    day_of_week: str,
    group_id: Optional[int] = None  # type: ignore
):
    # Базовый запрос с загрузкой связанных данных
    query = (
        select(Schedule)
        .options(
            joinedload(Schedule.subjects),
            joinedload(Schedule.users),
            joinedload(Schedule.cabinets),
            joinedload(Schedule.groups),
            joinedload(Schedule.attendance)
        )
    )
    
    # Применяем фильтры
    if day_of_week:
        query = query.where(Schedule.day_of_week == day_of_week)
    if group_id:
        query = query.where(Schedule.groups_idgroup == group_id)
    
    # Выполняем запрос
    schedules = (await session.execute(query)).unique().scalars().all()
    
    if not schedules:
        raise HTTPException(status_code=404, detail='Расписание не найдено')
    
    # Преобразуем в ответ
    result = []
    for schedule in schedules:
        # Получаем даты занятий из Attendance
        dates = [a.date.strftime("%d.%m.%Y") for a in schedule.attendance]
        
        # Преобразуем день недели из числа в текст
        day_names = {
            1: "Понедельник",
            2: "Вторник",
            3: "Среда",
            4: "Четверг",
            5: "Пятница",
            6: "Суббота"
        }
        
        result.append(ScheduleEntryResponse(
            idschedule=schedule.idschedule,
            time=schedule.time.strftime("%H:%M"),
            subject_name=schedule.subjects.name,
            teacher=ScheduleTeacherSchema(
                id=schedule.users.idusers,
                surname=schedule.users.surname,
                name=schedule.users.name,
                paternity=schedule.users.paternity
            ),
            cabinet=schedule.cabinets.idcabinet,  # или schedule.cabinets.name, если есть название
            group_name=schedule.groups.name if schedule.groups else None,
            day_of_week=day_names.get(schedule.day_of_week, "Неизвестно"),
            dates=dates
        ))
    
    return result

@router.get('/schedule/days')
async def get_schedule_by_days(
    session: AsyncSession,
    group_id: Optional[int] = None  # type: ignore
):
    day_mapping = {
        1: "Понедельник",
        2: "Вторник",
        3: "Среда",
        4: "Четверг",
        5: "Пятница",
        6: "Суббота"
    }
    
    result = {}
    for day_num, day_name in day_mapping.items():
        schedules = await get_schedule(session, day_of_week=day_num, group_id=group_id)
        result[day_name] = schedules
    
    return result
# @router.get('/schedule', response_model=list[SchedulesSchema], dependencies=[Depends(admin)])
# async def get_schedule(session: AsyncSessionDep):
#     schedules_stmt = (
#         select(Schedule, Cabinet, Subject, User)
#         .join(ScheduleCabinet, col(Schedule.id) == col(ScheduleCabinet.schedule_id))
#         .join(ScheduleSubject, col(Schedule.id) == col(ScheduleSubject.schedule_id))
#         .join(Cabinet, col(ScheduleCabinet.cabinet_id) == col(Cabinet.id))
#         .join(Subject, col(ScheduleSubject.subject_id) == col(Subject.id))
#         .join(User, col(Schedule.teacher_id) == col(User.id))
#         .where(User.role_id == 2)
#         .order_by(col(Schedule.dateandtime).asc())
#     )
#     schedules = (await session.execute(schedules_stmt)).all()
#     schedules_list: list[SchedulesSchema] = []

#     schedule: Schedule
#     cabinet: Cabinet
#     subject: Subject
#     teacher: User

#     for schedule, cabinet, subject, teacher in schedules:
#         if subject.type not in ('sport', 'art', 'free', 'paid'):
#             raise HTTPException(status_code=400, detail='Invalid subject type') 

#         sch = ScheduleSchema(
#             cabinet=cabinet.description,
#             date_n_time=schedule.dateandtime,
#             subject=SubjectSchema(
#                 id=subject.id,
#                 name=subject.name,
#                 description=subject.description,
#                 type=subject.type,
#             ),
#             teacher=TeacherSchema(
#                 name=teacher.name,
#                 surname=teacher.surname,
#                 paternity=teacher.paternity,
#             ),
#         )

#         is_added = False
#         for s in schedules_list:
#             if s.date == schedule.dateandtime.date():
#                 s.schedules.append(sch)
#                 is_added = True
#                 break

#         if not is_added:
#             schedules_list.append(
#                 SchedulesSchema(
#                     date=schedule.dateandtime.date(),
#                     day_name=schedule.dateandtime.strftime('%A'),
#                     schedules=[sch],
#                 )
#             )

#     return schedules_list

# опять таки неинтресно
# @router.post('/schedule', response_model=list[ScheduleSchema], dependencies=[Depends(admin)])
# async def create_schedule(session: AsyncSessionDep, schedule_data: ScheduleSchema):
#     cabinet_stmt = select(Cabinet).where(Cabinet.description == schedule_data.cabinet)
#     cabinet = (await session.execute(cabinet_stmt)).scalar_one_or_none()

#     if not cabinet or not cabinet.id:
#         cabinet = Cabinet(description=schedule_data.cabinet)
#         session.add(cabinet)

#     subject_stmt = select(Subject).where(Subject.name == schedule_data.subject.name)
#     subject = (await session.execute(subject_stmt)).scalar_one_or_none()

#     if not subject or not subject.id:
#         subject = Subject(
#             name=schedule_data.subject.name,
#             description=schedule_data.subject.description,
#             type=schedule_data.subject.type,
#         )
#         session.add(subject)

#     teacher_stmt = (
#         select(User)
#         .join(Role)
#         .where(Role.name == 'teacher')
#         .where(Role.id == User.role_id)
#         .where(User.name == schedule_data.teacher.name)
#         .where(User.surname == schedule_data.teacher.surname)
#         .where(User.paternity == schedule_data.teacher.paternity)
#     )
#     teacher = (await session.execute(teacher_stmt)).scalar_one_or_none()

#     if not teacher or not teacher.id:
#         raise HTTPException(status_code=404, detail='Teacher not found')

#     dates = [schedule_data.date_n_time + timedelta(weeks=i) for i in range(15)]
#     schedules: list[ScheduleSchema] = []

#     for date in dates:
#         schedule = Schedule(
#             dateandtime=date,
#             teacher_id=teacher.id,
#         )

#         session.add(schedule)
#         await session.commit()

#         await session.refresh(cabinet)
#         await session.refresh(subject)
#         await session.refresh(teacher)
#         await session.refresh(schedule)

#         if not schedule.id or not cabinet.id or not subject.id or not teacher.id:
#             raise HTTPException(status_code=500, detail='Internal Server Error')

#         s = ScheduleSubject(schedule_id=schedule.id, subject_id=subject.id)
#         c = ScheduleCabinet(schedule_id=schedule.id, cabinet_id=cabinet.id)

#         session.add(s)
#         session.add(c)
#         await session.commit()

#         await session.refresh(cabinet)
#         await session.refresh(subject)
#         await session.refresh(teacher)
#         await session.refresh(schedule)

#         schedules.append(
#             ScheduleSchema(
#                 cabinet=cabinet.description,
#                 date_n_time=schedule.dateandtime,
#                 subject=SubjectSchema(
#                     id=subject.id,
#                     name=subject.name,
#                     description=subject.description,
#                     type=schedule_data.subject.type,
#                 ),
#                 teacher=TeacherSchema(
#                     name=teacher.name,
#                     surname=teacher.surname,
#                     paternity=teacher.paternity,
#                 ),
#             )
#         )

#     return schedules
