from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from apps.users.models import (
    Users, Roles, Attendance, t_scheduleshow, t_subjectsshow 
)
from apps.users.schema import (
    BearerSchema, LoginSchema, ScheduleTeacherSchema, 
    SubjectSchema, ScheduleEntryResponse, ScheduleEntrySchema, UserCreateSchema # type: ignore
)
from database.manager import AsyncSession
from  middlewares.security import encode, SECRET_KEY, ALGORITHM
from middlewares.security import student_required, teacher_required  

common_router = APIRouter(prefix="/api", tags=["Common"])

# Роутер только для преподавателей
teacher_router = APIRouter(
    prefix="/teacher",
    tags=["Teacher"],
    dependencies=[Depends(teacher_required)]
)

# Роутер только для учеников
student_router = APIRouter(
    prefix="/student",
    tags=["Student"],
    dependencies=[Depends(student_required)]
)

# Общий роутер для аутентификации
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# @auth_router.post('/login', response_model=BearerSchema)
# async def login(
#     session: AsyncSession = Depends(get_session),
#     login_data: LoginSchema = Depends()
# ):
#     # Ищем пользователя по логину и паролю
#     user = (await session.execute(
#         select(Users)
#         .where(Users.login == login_data.login)
#         .where(Users.password == login_data.password)
#     )).scalar_one_or_none()

#     if not user:
#         raise HTTPException(status_code=404, detail='Пользователь не найден')

#     # Получаем роль пользователя
#     role = (await session.execute(
#         select(Roles).where(Roles.idroles == user.roles_idroles)
#     )).scalar_one()

#     # Генерируем токен (ваша текущая реализация)
#     encoded_jwt = str(encode(
#         {"role": role.name, "user_id": user.idusers},
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     ))

#     return BearerSchema(
#         access_token=encoded_jwt,
#         role=role.name
#     )

# @common_router.get('/users', response_model=list[Users])
# async def get_users(session: AsyncSession = Depends(get_session)):
#     return (await session.execute(select(Users))).scalars().all()

# @common_router.post('/users', response_model=Users)
# async def create_user(session: AsyncSession = Depends(get_session), user: UserCreateSchema = Depends()):
#     u = Users(
#         surname=user.surname,
#         name=user.name,
#         paternity=user.paternity,
#         birthdate=user.birthdate,
#         login=user.login,
#         password=user.password,
#         roles_idroles=user.role_id,  # Исправлено: roles_idroles вместо role_id
#     )
#     session.add(u)
#     await session.commit()
#     await session.refresh(u)
#     return u

# @common_router.get('/teachers', response_model=list[Users])
# async def get_teachers(session: AsyncSession = Depends(get_session)):
#     return (await session.execute(select(Users).where(Users.roles_idroles == 2))).scalars().all()

# @common_router.get('/subjects', response_model=list[SubjectSchema])
# async def get_subjects(session: AsyncSession = Depends(get_session)):
#     # Получаем все предметы из представления
#     subjects = (await session.execute(
#         select(t_subjectsshow)
#     )).scalars().all()

#     if not subjects:
#         raise HTTPException(status_code=404, detail='Предметы не найдены')

#     return subjects

# @common_router.get('/schedule', response_model=list[ScheduleEntrySchema])
# async def get_schedule(
#     session: AsyncSession = Depends(get_session),
#     day_of_week: str,
#     group_id: int | None
# ):
#     # Базовый запрос к представлению
#     query = select(t_scheduleshow)

#     # Применяем фильтры
#     if day_of_week:
#         query = query.where(t_scheduleshow.c.day_of_week == day_of_week)
#     if group_id:
#         query = query.where(t_scheduleshow.c.group_nam == str(group_id))

#     # Выполняем запрос
#     result = (await session.execute(query)).all()

#     if not result:
#         raise HTTPException(status_code=404, detail='Расписание не найдено')

#     # Форматируем ответ
#     return [
#         ScheduleEntrySchema(
#             idschedule=row.idschedule,
#             time=row.time.strftime("%H:%M"),
#             subject_name=row.subject_name,
#             teacher=ScheduleTeacherSchema.from_string(row.teacher),
#             cabinet=str(row.cabinet),
#             group_name=row.group_nam,
#             day_of_week=row.day_of_week
#         )
#         for row in result
#     ]

# @common_router.get('/schedule/days', response_model=dict[str, list[ScheduleEntrySchema]])
# async def get_schedule_by_days(
#     session: AsyncSession = Depends(get_session),
#     group_id: int | None
# ) -> dict[str, list[ScheduleEntrySchema]]:  # Явное указание типа возвращаемого значения
#     days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
#     result: dict[str, list[ScheduleEntrySchema]] = {}  # Явная аннотация типа

#     for day in days:
#         schedules = await get_schedule(session, day_of_week=day, group_id=group_id)
#         if schedules:
#             result[day] = schedules

#     return result

# @common_router.get('/schedule/{schedule_id}/dates', response_model=list[str])
# async def get_schedule_dates(
#     schedule_id: int,
#     session: AsyncSession = Depends(get_session)
# ):
#     dates = (await session.execute(
#         select(Attendance.date)
#         .where(Attendance.idschedule == schedule_id)
#         .order_by(Attendance.date)
#     )).scalars().all()

#     return [date.strftime("%d.%m.%Y") for date in dates]

# Регистрация роутеров
router = APIRouter()
router.include_router(auth_router)
router.include_router(common_router)
router.include_router(teacher_router)
router.include_router(student_router)

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


@router.get('/users', response_model=list[Users])
async def get_users(session: AsyncSession):
    return (await session.execute(select(Users))).scalars().all()


# @router.post('/users', response_model=Users, dependencies=[Depends(admin)])
# async def create_user(session: AsyncSession, user: UserCreateSchema):
#     u = Users(
#         surname=user.surname,
#         name=user.name,
#         paternity=user.paternity,
#         birthdate=user.birthdate,
#         login=user.login,
#         password=user.password,
#         role_id=user.role_id,
#     )
#     session.add(u)
#     await session.commit()
#     await session.refresh(u)
#     return u


@router.get('/teachers', response_model=list[Users], dependencies=[Depends(student_required)])
async def get_teachers(session: AsyncSession):
    return (await session.execute(select(Users).where(Users.roles_idroles == 2))).scalars().all()

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

@router.get('/schedule', response_model=list[ScheduleEntrySchema])
async def get_schedule(
    session: AsyncSession,
    day_of_week: str,
    group_id: int | None
):
    # Базовый запрос к представлению
    query = select(t_scheduleshow)
    
    # Применяем фильтры
    if day_of_week:
        query = query.where(t_scheduleshow.c.day_of_week == day_of_week)
    if group_id:
        query = query.where(t_scheduleshow.c.group_nam == str(group_id))
    
    # Выполняем запрос
    result = (await session.execute(query)).all()
    
    if not result:
        raise HTTPException(status_code=404, detail='Расписание не найдено')
    
    # Форматируем ответ
    return [
        ScheduleEntrySchema(
            idschedule=row.idschedule,
            time=row.time.strftime("%H:%M"),
            subject_name=row.subject_name,
            teacher=ScheduleTeacherSchema.from_string(row.teacher),
            cabinet=str(row.cabinet),
            group_name=row.group_nam,
            day_of_week=row.day_of_week
        )
        for row in result
    ] 

@router.get('/schedule/days', response_model=dict[str, list[ScheduleEntrySchema]])
async def get_schedule_by_days(
    session: AsyncSession,
    group_id: int | None = None
) -> dict[str, list[ScheduleEntrySchema]]:
    days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
    result: dict[str, list[ScheduleEntrySchema]] = {}
    
    for day in days:
        schedules = await get_schedule(session, day_of_week=day, group_id=group_id)
        if schedules:
            result[day] = schedules

    return result

@router.get('/schedule/{schedule_id}/dates', response_model=list[str])
async def get_schedule_dates(
    schedule_id: int,
    session: AsyncSession
):
    dates = (await session.execute(
        select(Attendance.date)
        .where(Attendance.idschedule == schedule_id)
        .order_by(Attendance.date)
    )).scalars().all()
    
    return [date.strftime("%d.%m.%Y") for date in dates]