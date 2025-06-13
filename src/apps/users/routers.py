import logging 
import os
from fastapi import APIRouter, Depends, HTTPException, Body
from datetime import date, datetime, timezone, timedelta  # type: ignore
from fastapi.param_functions import Query
from sqlalchemy import case, select , func 
from starlette.responses import FileResponse
import yagmail

from apps.users.models import (
    Users, Roles, Attendance, Types, t_scheduleshow, t_scheduleshow_extra, t_subjects_with_types, t_usersshow, t_usersshow_with_birthdate, 
    Subjects, Groups, GroupsUsers, Schedule, BilNebil# type: ignore
)
from apps.users.schema import (
    BearerSchema, LoginSchema, UserResponseSchema, TypeSchema, GroupSchema, 
    SubjectSchema, ScheduleEntrySchema, ScheduleExtraSchema, UpdateAttendanceRequest, 
    UserResponseSchemaBithdate, ScheduleDateSchema, AttendanceRecordSchema, BilNebilSchema, DayScheduleSchema # type: ignore
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
    
@router.post('/logout')
async def logout():
    # На backend обычно просто удаляют/аннулируют refresh токен, если хранится
    # Здесь можно реализовать логику очистки сессии, если есть
    return {"detail": "Logged out"}

    
@router.get('/documentation/download')
async def download_documentation():
    doc_path = 'static/docs/documentation.pdf'  # путь к файлу с документацией
    if not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Documentation not found")
    return FileResponse(path=doc_path, filename="documentation.pdf", media_type='application/pdf') 

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

async def send_email(to: str, subject: str, body: str):
    """Отправляет email с использованием yagmail.  Обратите внимание на обработку ошибок."""
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")

    if not sender or not password:
        raise HTTPException(status_code=500, detail="Email configuration missing.")
    try:
        yag = yagmail.SMTP(sender, password) # type: ignore
        yag.send(to=to, subject=subject, contents=body) # type: ignore
    except Exception as e:
        # Логирование ошибки здесь критически важно для отладки
        print(f"Error sending email: {e}")  # Запись ошибки в консоль
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}") from e # Передача исключения вверх

@router.post('/enroll/group')
async def enroll_to_group(
    group_id: int = Body(..., embed=True),
    current_user_id: int = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
    session: AsyncSession = Depends(get_session)
):
    if current_user_role != "Ученик":
        raise HTTPException(status_code=403, detail="Only students can enroll")
    
    try:
        # Проверка на существование группы и пользователя (добавлено)
        group = await session.get(Groups, group_id)
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")
        user = await session.get(Users, current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")


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
        if count > 20: # type: ignore
            raise HTTPException(status_code=400, detail="Group is full")

        new_enrollment = GroupsUsers(
            groups_idgroups=group_id,
            users_idusers=current_user_id
        )
        session.add(new_enrollment)
        await session.commit()
        await session.refresh(new_enrollment) # Добавлено для получения ID


        # Отправка уведомления
        if user and user.login: 
            return {"message": "Enrollment successful"} # Возвращаем ID записи
            # await send_email(
            #     to=user.login, # Используем email
            #     subject="Запись на занятие",
            #     body=f"Вы успешно записаны на группу {group.name}. Обратите внимание, что для подтверждения необходимо обратиться к администрации."
            # )

       

    except Exception as e:
        await session.rollback()  # Очень важно откатить транзакцию при ошибке
        raise HTTPException(status_code=500, detail=f"Server error: {e}") from e


@router.get("/common_schedule", response_model=list[ScheduleEntrySchema])
async def get_common_schedule(
    session: AsyncSession = Depends(get_session)
) -> list[ScheduleEntrySchema]:
    """Получение общего расписания для всех ролей"""
    try:
        result = await session.execute(
            select(t_scheduleshow)
            .order_by(t_scheduleshow.c.day_of_week, t_scheduleshow.c.time)
        )
        
        schedules = result.mappings().all()
        
        if not schedules:
            return []
            
        return [
            ScheduleEntrySchema(
                idschedule=item["idschedule"],
                time=item["time"].strftime("%H:%M"),
                subject_name=item["subject_name"],
                teacher=item["teacher"],
                cabinet=str(item["cabinet"]),
                group_nam=item["group_nam"],
                day_of_week=item["day_of_week"]
            )
            for item in schedules
        ]
    except Exception as e:
        logger.error(f"Error in get_common_schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/personal_schedule", response_model=list[ScheduleExtraSchema])
async def get_personal_schedule(
    current_user: BearerSchema = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> list[ScheduleExtraSchema]:
    """
    Получение персонального расписания для текущего пользователя
    - Для преподавателя: его занятия
    - Для студента: занятия всех его групп
    Возвращает список занятий
    """
    try:
        if current_user.role == "Преподаватель":
            # Для преподавателя - занятия где он ведет
            query = select(t_scheduleshow_extra).where(
                t_scheduleshow_extra.c.teacher_id == current_user.user_id
            )
        elif current_user.role == "Ученик":
            # Для студента - находим ВСЕ его группы
            group_result = await session.execute(
                select(GroupsUsers.groups_idgroups)
                .where(GroupsUsers.users_idusers == current_user.user_id)
            )
            group_ids = [row[0] for row in group_result.all()]
            
            if not group_ids:
                return []
                
            # И берем расписание всех его групп
            query = select(t_scheduleshow_extra).where(
                t_scheduleshow_extra.c.group_id.in_(group_ids)
            )
        else:
            return []
            
        # Выполняем запрос и сортируем по дню недели и времени
        result = await session.execute(
            query.order_by(t_scheduleshow_extra.c.day_of_week, t_scheduleshow_extra.c.time)
        )
        schedules = result.mappings().all()
        
        return [
            ScheduleExtraSchema(
                idschedule=item["idschedule"],
                time=item["time"].strftime("%H:%M"),
                subject_name=item["subject_name"],
                teacher=item["teacher"],
                teacher_id=item["teacher_id"],
                cabinet=str(item["cabinet"]),
                group_id=item["group_id"],
                group_nam=item["group_nam"],
                day_of_week=item["day_of_week"]
            )
            for item in schedules
        ]
    except Exception as e:
        logger.error(f"Error in get_personal_schedule: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# @router.get("/schedule/{schedule_id}/dates", response_model=list[ScheduleDateSchema])
# async def get_schedule_dates(
#     schedule_id: int,
#     current_user: BearerSchema = Depends(get_current_user),
#     session: AsyncSession = Depends(get_session)
# ):
#     try:
#         # Verify schedule exists
#         schedule = await session.get(Schedule, schedule_id)
#         if not schedule:
#             raise HTTPException(status_code=404, detail="Schedule not found")
        
#         # Base query
#         query = select(
#             Attendance.idattendance,
#             Attendance.date,
#             func.bool_or(BilNebil.status).label("has_attendance")
#         ).outerjoin(
#             BilNebil, BilNebil.idattendance == Attendance.idattendance
#         ).where(
#             Attendance.idschedule == schedule_id
#         )
        
#         # For students, get their individual status
#         if current_user.role == "Ученик":
#             query = query.add_columns(
#                 func.max(
#                     case(
#                         (BilNebil.iduser == current_user.user_id, BilNebil.status),
#                         else_=None
#                     )
#                 ).label("student_status")
#             ).group_by(Attendance.idattendance, Attendance.date)
#         else:
#             query = query.group_by(Attendance.idattendance, Attendance.date)
        
#         result = await session.execute(query.order_by(Attendance.date))
        
#         return [
#             ScheduleDateSchema(
#                 idattendance=row.idattendance,
#                 date=row.date.strftime("%Y-%m-%d"),
#                 attendance_status=row.student_status if current_user.role == "Ученик" else row.has_attendance
#             )
#             for row in result.all()
#         ]
        
#     except Exception as e:
#         logger.error(f"Error in get_schedule_dates: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/schedule/{schedule_id}/dates", response_model=list[ScheduleDateSchema])
async def get_schedule_dates(
    schedule_id: int,
    current_user: BearerSchema = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Verify schedule exists
        schedule = await session.get(Schedule, schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        if current_user.role == "Ученик":
            # For students - get dates with their individual status
            query = (
                select(
                    Attendance.idattendance,
                    Attendance.date,
                    func.max(
                        case(
                            (BilNebil.iduser == current_user.user_id, BilNebil.status),
                            else_=None
                        )
                    ).label("student_status")
                )
                .outerjoin(
                    BilNebil, BilNebil.idattendance == Attendance.idattendance
                )
                .where(Attendance.idschedule == schedule_id)
                .group_by(Attendance.idattendance, Attendance.date)
                .order_by(Attendance.date)
            )
        else:
            # For teachers/admin - get dates with group attendance status
            query = (
                select(
                    Attendance.idattendance,
                    Attendance.date,
                    func.bool_or(BilNebil.status).label("has_attendance")
                )
                .outerjoin(
                    BilNebil, BilNebil.idattendance == Attendance.idattendance
                )
                .where(Attendance.idschedule == schedule_id)
                .group_by(Attendance.idattendance, Attendance.date)
                .order_by(Attendance.date)
            )
        
        result = await session.execute(query)
        
        return [
            ScheduleDateSchema(
                idattendance=row.idattendance,
                date=row.date.strftime("%Y-%m-%d"),
                attendance_status=row.student_status if current_user.role == "Ученик" else row.has_attendance
            )
            for row in result.all()
        ]
        
    except Exception as e:
        logger.error(f"Error in get_schedule_dates: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/by-attendance", response_model=list[AttendanceRecordSchema])
async def get_attendance_by_attendance_id(
    attendance_id: int = Query(..., alias="attendance_id"), 
    current_user: BearerSchema = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Получает записи посещаемости для конкретного attendance (аналог C# метода GetAttendanceData)"""
    try:
        # 1. Получаем attendance и проверяем его существование
        attendance = await session.execute(
            select(Attendance)
            .where(Attendance.idattendance == attendance_id)
        )
        attendance = attendance.scalar_one_or_none()
        
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance not found")
        
        # 2. Получаем schedule_id из attendance
        schedule_id = attendance.idschedule
        
        # 3. Проверяем доступ пользователя к этому расписанию
        if current_user.role == "Преподаватель":
            schedule_check = await session.execute(
                select(Schedule)
                .where(
                    Schedule.idschedule == schedule_id,
                    Schedule.users_idusers == current_user.user_id
                )
            )
        elif current_user.role == "Ученик":
            schedule_check = await session.execute(
                select(Schedule)
                .join(GroupsUsers, GroupsUsers.groups_idgroups == Schedule.groups_idgroup)
                .where(
                    Schedule.idschedule == schedule_id,
                    GroupsUsers.users_idusers == current_user.user_id
                )
            )
        else:
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        if not schedule_check.scalar():
            raise HTTPException(status_code=404, detail="Расписание не найдено или нет доступа")
        
        # 4. Получаем данные о студентах и их посещаемости (аналог C# query)
        query = (
            select(
                Users.idusers.label("iduser"),
                (Users.surname + " " + Users.name + " " + (Users.paternity or "")).label("full_name"),
                BilNebil.status
            )
            .select_from(Users)
            .join(GroupsUsers, GroupsUsers.users_idusers == Users.idusers)
            .join(Schedule, Schedule.groups_idgroup == GroupsUsers.groups_idgroups)
            .outerjoin(
                BilNebil,
                (BilNebil.idattendance == attendance_id) & 
                (BilNebil.iduser == Users.idusers)
            )
            .where(Schedule.idschedule == schedule_id)
            .order_by(Users.surname, Users.name)
        )
        
        result = await session.execute(query)
        records = result.all()
        
        return [
            AttendanceRecordSchema(
                iduser=record.iduser,
                full_name=record.full_name,
                status=record.status
            )
            for record in records
        ]
        
    except Exception as e:
        logger.error(f"Error in get_attendance_by_attendance_id: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/update")
async def update_attendance(
    data: UpdateAttendanceRequest,
    session: AsyncSession = Depends(get_session),
    current_user: BearerSchema = Depends(get_current_user)
):
    """Обновляет статусы посещаемости для указанного idattendance."""
    try:
        # 1. Check attendance exists
        attendance = await session.execute(
            select(Attendance)
            .where(Attendance.idattendance == data.idattendance)
        )
        attendance = attendance.scalar_one_or_none()
        
        if not attendance:
            raise HTTPException(status_code=404, detail="Attendance not found")

        # 2. Date validation (current day ± 14 days)
        today = date.today()
        attendance_date = attendance.date
        min_allowed_date = today - timedelta(days=14)
        max_allowed_date = today + timedelta(days=14)

        if attendance_date > max_allowed_date:
            raise HTTPException(
                status_code=400,
                detail="Cannot mark attendance more than 2 weeks in advance"
            )
        if attendance_date < min_allowed_date:
            raise HTTPException(
                status_code=400,
                detail="Can only mark attendance for the last 2 weeks"
            )

        # 3. Check user permissions
        if current_user.role == "Преподаватель":
            schedule_check = await session.execute(
                select(Schedule)
                .where(
                    Schedule.idschedule == attendance.idschedule,
                    Schedule.users_idusers == current_user.user_id
                )
            )
        elif current_user.role == "Ученик":
            schedule_check = await session.execute(
                select(Schedule)
                .join(GroupsUsers, GroupsUsers.groups_idgroups == Schedule.groups_idgroup)
                .where(
                    Schedule.idschedule == attendance.idschedule,
                    GroupsUsers.users_idusers == current_user.user_id
                )
            )
        else:
            raise HTTPException(status_code=403, detail="Access denied")

        if not schedule_check.scalar():
            raise HTTPException(status_code=403, detail="No access to schedule")

        # 4. Process updates
        for user_id, status in data.updates.items():
            existing = await session.execute(
                select(BilNebil)
                .where(
                    BilNebil.idattendance == data.idattendance,
                    BilNebil.iduser == user_id
                )
            )
            record = existing.scalar_one_or_none()

            if record:
                if status is None:
                    await session.delete(record)
                else:
                    record.status = status
            elif status is not None:
                new_record = BilNebil(
                    idattendance=data.idattendance,
                    iduser=user_id,
                    status=status
                )
                session.add(new_record)

        await session.commit()
        return {"message": "Attendance updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error in update_attendance: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )