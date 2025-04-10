
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select , func

from apps.users.models import (
    Users, Roles, Attendance, Types, t_scheduleshow, t_subjects_with_types, t_usersshow, Subjects, Groups, GroupsUsers # type: ignore
)
from apps.users.schema import (
    BearerSchema, LoginSchema, UserResponseSchema, TypeSchema, GroupSchema, 
    SubjectSchema, ScheduleEntryResponse, ScheduleEntrySchema # type: ignore
)
from database.manager import AsyncSession, get_session

from middlewares.security import encode, SECRET_KEY, ALGORITHM
from middlewares.security import student_required, teacher_required, get_current_user_id, get_current_user_role

common_router = APIRouter(prefix="/api", tags=["Common"])
teacher_router = APIRouter(prefix="", tags=["Teacher"], dependencies=[Depends(teacher_required)])
student_router = APIRouter(prefix="", tags=["Student"], dependencies=[Depends(student_required)])
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

router = APIRouter()
router.include_router(auth_router)
router.include_router(common_router)
router.include_router(teacher_router)
router.include_router(student_router)

@router.get("/protected-route")
async def protected_route(
    current_user_id: int = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role)
):
    # Ваша логика
    return {"message": "Доступ разрешен"}

@router.post('/login', response_model=BearerSchema)
async def login( 
    login_data: LoginSchema, 
    session: AsyncSession = Depends(get_session)
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
        role=role.name,
        token_type="bearer"
    )

@router.get('/users', response_model=list[UserResponseSchema])
async def get_users(session: AsyncSession = Depends(get_session)):
    query = select(t_usersshow)  # Представление должно содержать все нужные поля
    result = await session.execute(query)
    return result.mappings().all()

@router.get('/teachers', response_model=list[UserResponseSchema])
async def get_teachers(session: AsyncSession = Depends(get_session)):
    query = select(t_usersshow).where(t_usersshow.c.idroles == 2)
    result = await session.execute(query)
    return result.mappings().all() 

# @router.get('/subjects', response_model=list[SubjectSchema])
# async def get_subjects(session: AsyncSession = Depends(get_session)):
#     query = select(t_subjects_with_types)
#     result = await session.execute(query)
#     subjects = result.mappings().all()
    
#     if not subjects:
#         raise HTTPException(status_code=404, detail='Предметы не найдены')
    
#     # Преобразуем данные к нужному формату
#     formatted_subjects: list[dict[str, Any]] = []
#     for subj in subjects:
#         formatted_types: list[dict[str, Any]] = []
#         if subj.types:
#             for type_data in subj.types:
#                 formatted_types.append({
#                     "id": type_data.get("id"), 
#                     "type": type_data.get("type")  
#                 })
        
#         formatted_subjects.append({
#             "subject_id": subj.subject_id,
#             "subject_name": subj.subject_name,
#             "description": subj.description or "",
#             "types": formatted_types
#         })
    
#     return formatted_subjects 

# @router.get('/subjects', response_model=list[SubjectSchema])
# async def get_subjects( # type: ignore
#     session: AsyncSession = Depends(get_session)
# ):
#     query = select(t_subjects_with_types)
#     result = await session.execute(query)
#     subjects = result.mappings().all()
    
#     return [
#         {
#             "subject_id": subj.subject_id,
#             "subject_name": subj.subject_name,
#             "description": subj.description or "",
#             "types": subj.types or []  # JSON автоматически преобразуется в список словарей
#         }
#         for subj in subjects
#     ] # type: ignore 




@router.get('/subjects', response_model=list[SubjectSchema])
async def get_subjects(
    session: AsyncSession = Depends(get_session)
) -> list[SubjectSchema]:
    """
    Получение списка предметов с валидацией через Pydantic.
    """
    result = await session.execute(select(t_subjects_with_types))
    rows = result.mappings().all()
    
    # Явное преобразование с валидацией
    return [SubjectSchema(**dict(row)) for row in rows] 
 
@router.get('/groups', response_model=list[GroupSchema])
async def get_groups(
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(Groups))
    rows = result.scalars().all()
    return rows

@router.get('/types', response_model=list[TypeSchema])
async def get_types(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Types))
    types = result.scalars().all()
    return types

# @router.post('/enroll/group')
# async def enroll_to_group(
#     idgroups: int,  # Принимаем JSON с groupId
#     current_user_id: int = Depends(get_current_user_id),
#     current_user_role: str = Depends(get_current_user_role),
#     session: AsyncSession = Depends(get_session)
# ):
#     if current_user_role != "Ученик":
#         raise HTTPException(status_code=403, detail="Only students can enroll")

#     if not idgroups:
#         raise HTTPException(status_code=400, detail="Group ID is required")

#     # Проверяем, не записан ли уже пользователь
#     existing = await session.execute(
#         select(GroupsUsers).where(
#             GroupsUsers.groups_idgroups == idgroups,
#             GroupsUsers.users_idusers == current_user_id
#         )
#     )
#     if existing.scalar():
#         raise HTTPException(status_code=400, detail="Already enrolled")

#     # Проверяем количество записей для группы
#     count = await session.execute(
#         select(func.count()).select_from(GroupsUsers).where(GroupsUsers.groups_idgroups == idgroups)
#     )
#     if count.scalar() >= 20: # type: ignore
#         raise HTTPException(status_code=400, detail="Group is full")

#     # Добавляем запись
#     enrollment = GroupsUsers(
#         groups_idgroups=idgroups,
#         users_idusers=current_user_id
#     )
#     session.add(enrollment)
#     await session.commit()

#     return {"message": "Enrollment successful"}  

    
@router.post('/enroll/group')
async def enroll_to_group( 
    request: Request,
    group_id: int,  # Принимаем ID группы напрямую из тела запроса
    current_user_id: int = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    session: AsyncSession = Depends(get_session)
):
    print(f"Токен: {request.headers.get('authorization')}")  # Для отладки
    print(f"Данные: {await request.body()}")  # type: ignore 

    if current_user_role != "Ученик":
        raise HTTPException(status_code=403, detail="Only students can enroll")

    # Проверяем существующую запись
    existing = await session.execute(
        select(GroupsUsers).where(
            GroupsUsers.groups_idgroups == group_id,
            GroupsUsers.users_idusers == current_user_id
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Already enrolled")

    # Проверяем количество участников группы
    count = await session.scalar(
        select(func.count()).where(GroupsUsers.groups_idgroups == group_id)
    )
    
    if count >= 20: # type: ignore
        raise HTTPException(status_code=400, detail="Group is full")

    # Создаем запись
    session.add(GroupsUsers(
        groups_idgroups=group_id,
        users_idusers=current_user_id
    ))
    await session.commit()

    return {"message": "Enrollment successful"}

@router.get("/schedule", response_model=list[ScheduleEntrySchema])
async def get_schedule(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id), 
    role: str = Depends(get_current_user_role)
) -> list[ScheduleEntrySchema]:
    """
    Получение расписания в зависимости от роли пользователя
    """
    if role == "Ученик":
        # Логика для ученика
        groups_query = select(GroupsUsers).where(GroupsUsers.users_idusers == user_id)
        user_groups = (await session.execute(groups_query)).scalars().all()
        
        if not user_groups:
            return []
        
        group_ids = [group.groups_idgroups for group in user_groups]
        
        schedule_query = (
            select(t_scheduleshow)
            .where(t_scheduleshow.c.groups_idgroup.in_(group_ids))
            .order_by(t_scheduleshow.c.day_of_week, t_scheduleshow.c.time)
        )
    elif role == "Преподаватель":
        # Логика для преподавателя
        schedule_query = (
            select(t_scheduleshow)
            .where(t_scheduleshow.c.users_idusers == user_id)
            .order_by(t_scheduleshow.c.day_of_week, t_scheduleshow.c.time)
        )
    else:
        # Для админа или других ролей
        schedule_query = select(t_scheduleshow).order_by(t_scheduleshow.c.day_of_week, t_scheduleshow.c.time)
    
    schedule = (await session.execute(schedule_query)).scalars().all()
    return schedule # type: ignore


# @router.get('/schedule/days', response_model=dict[str, list[ScheduleEntrySchema]])
# async def get_schedule_by_days(
#     group_id: int | None = None,
#     session: AsyncSession = Depends(get_session)
# ) -> dict[str, list[ScheduleEntrySchema]]:
#     days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота"]
#     result: dict[str, list[ScheduleEntrySchema]] = {}
    
#     for day in days:
#         schedules = await get_schedule(day_of_week=day, group_id=group_id, session=session)
#         if schedules:
#             result[day] = schedules

#     return result

@router.get('/schedule/{schedule_id}/dates', response_model=list[str])
async def get_schedule_dates(
    schedule_id: int,
    session: AsyncSession = Depends(get_session)
):
    dates = (await session.execute(
        select(Attendance.date)
        .where(Attendance.idschedule == schedule_id)
        .order_by(Attendance.date)
    )).scalars().all()
    
    return [date.strftime("%d.%m.%Y") for date in dates]