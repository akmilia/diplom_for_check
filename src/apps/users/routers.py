import logging
from fastapi import APIRouter, Depends, HTTPException, Body
from datetime import datetime, timezone, timedelta
from sqlalchemy import select , func 

from apps.users.models import (
    Users, Roles, Attendance, Types, t_scheduleshow, t_subjects_with_types, t_usersshow, t_usersshow_with_birthdate, Subjects, Groups, GroupsUsers, Schedule# type: ignore
)
from apps.users.schema import (
    BearerSchema, LoginSchema, UserResponseSchema, TypeSchema, GroupSchema, 
    SubjectSchema, ScheduleEntrySchema, UserResponseSchemaBithdate, ScheduleTeacherSchema
)
from database.manager import AsyncSession, get_session
from jose import jwt, JWTError

from middlewares.security import SECRET_KEY, ALGORITHM
from middlewares.security import get_current_user_id, get_current_user_role, create_tokens, get_current_user

router = APIRouter(prefix="/api")

@router.get("/debug/token-info")
async def debug_token_info(
    current_user: BearerSchema = Depends(get_current_user)
):
    """Endpoint for debugging token structure"""
    return {
        "token_data": current_user.dict(), # type: ignore
        "is_valid": True,
        "current_time": datetime.now(timezone.utc).isoformat()
    }

@router.post('/login', response_model=BearerSchema)
async def login(login_data: LoginSchema, session: AsyncSession = Depends(get_session)):
    user = (await session.execute(
        select(Users)
        .where(Users.login == login_data.login)
        .where(Users.password == login_data.password)
    )).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='Пользователь не найден')

    role = (await session.execute(
        select(Roles).where(Roles.idroles == user.roles_idroles)
    )).scalar_one() 

    if role.idroles not in (2, 3):
        raise HTTPException(status_code=404, detail='Работа такой роли не предусмотрена в этом приложении')

    tokens = create_tokens(user.idusers, role.name)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    return BearerSchema(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type= "bearer", 
        user_id=user.idusers,
        role=role.name,
        expires_in=1800,
        expires_at=expires_at
    ) 

@router.post('/refresh', response_model=BearerSchema)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    session: AsyncSession = Depends(get_session)
):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        
        user = await session.get(Users, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        role = (await session.execute(
            select(Roles).where(Roles.idroles == user.roles_idroles)
        )).scalar_one()

        tokens = create_tokens(user.idusers, role.name)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        return BearerSchema(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type= "bearer",
            user_id=user.idusers,
            role=role.name,
            expires_in=1800,
            expires_at=expires_at
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get('/users', response_model=list[UserResponseSchema])
async def get_users(session: AsyncSession = Depends(get_session)):
    query = select(t_usersshow) 
    result = await session.execute(query)
    return result.mappings().all() 

@router.get('/teachers', response_model=list[UserResponseSchema])
async def get_teachers(session: AsyncSession = Depends(get_session)):
    query = select(t_usersshow).where(t_usersshow.c.idroles == 2)
    result = await session.execute(query)
    return result.mappings().all()  

logger = logging.getLogger(__name__) 
@router.get('/current-user', response_model=UserResponseSchemaBithdate)
async def get_current_user_profile(
    current_user: BearerSchema = Depends(get_current_user),  
    session: AsyncSession = Depends(get_session)
):
    try:
        query = select(t_usersshow_with_birthdate).where(
            t_usersshow_with_birthdate.c.idusers == current_user.user_id  
        )
        result = await session.execute(query)
        user = result.mappings().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "idusers": user["idusers"],
            "full_name": user["full_name"],
            "login": user["login"],
            "birthdate": user["birthdate"].isoformat() if user["birthdate"] else None,
            "id_roles": user["idroles"],
            "user_role": user["user_role"]
        }
    except Exception as e:
        logger.error(f"Current user error: {str(e)}")
        raise HTTPException(500, "Internal server error")


@router.get('/user-courses', response_model=list[str]) 
async def get_user_courses(
   current_user: BearerSchema = Depends(get_current_user),  
   session: AsyncSession = Depends(get_session)
) -> list[str]:  # Добавляем аннотацию типа возвращаемого значения
   
    if current_user.role == "Преподаватель":
        result = await session.execute(
            select(Subjects.name)
            .join(Schedule, Schedule.subjects_idsubjects == Subjects.idsubjects)
            .where(Schedule.users_idusers == current_user.user_id)
            .distinct()
        )
    elif current_user.role == "Ученик":
        result = await session.execute(
            select(Groups.name)
            .join(GroupsUsers, GroupsUsers.groups_idgroups == Groups.idgroups)
            .where(GroupsUsers.users_idusers == current_user.user_id)
        )
    else:
        return []
    
    return [row[0] for row in result.all()]

@router.get('/subjects', response_model=list[SubjectSchema])
async def get_subjects(
    session: AsyncSession = Depends(get_session)
) -> list[SubjectSchema]:
    result = await session.execute(select(t_subjects_with_types))
    rows = result.mappings().all()
    
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
    group_id: int = Body(..., embed=True),
    current_user_id: int = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    session: AsyncSession = Depends(get_session)
):
    if current_user_role != "Ученик":
        raise HTTPException(status_code=403, detail="Only students can enroll")

    existing = await session.execute(
        select(GroupsUsers).where(
            GroupsUsers.groups_idgroups == group_id,
            GroupsUsers.users_idusers == current_user_id
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="Already enrolled")

    count = await session.scalar(
        select(func.count()).where(GroupsUsers.groups_idgroups == group_id)
    )

    if count >= 20:  # type: ignore
        raise HTTPException(status_code=400, detail="Group is full")

    session.add(GroupsUsers(
        groups_idgroups=group_id,
        users_idusers=current_user_id
    ))
    await session.commit()

    return {"message": "Enrollment successful"}

@router.get("/common_schedule", response_model=list[ScheduleEntrySchema])
async def get_common_schedule(
    session: AsyncSession = Depends(get_session),
) -> list[ScheduleEntrySchema]:
    """Получение общего расписания для всех ролей"""
    try:
        # Используем mappings() чтобы получить словари вместо кортежей
        result = await session.execute(
            select(t_scheduleshow)
            .order_by(t_scheduleshow.c.day_of_week, t_scheduleshow.c.time)
        )
        
        schedules = result.mappings().all()
        
        # Преобразуем данные в соответствии с моделью ScheduleEntrySchema
        return [
            ScheduleEntrySchema(
                idschedule=item["idschedule"],
                time=item["time"].strftime("%H:%M"),  # Преобразуем время в строку
                subject_name=item["subject_name"],
                teacher=ScheduleTeacherSchema.from_string(item["teacher"]),
                cabinet=str(item["cabinet"]),
                group_name=item["group_name"],
                day_of_week=item["day_of_week"]
            )
            for item in schedules
        ]
    except Exception as e:
        logger.error(f"Error fetching common schedule: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

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