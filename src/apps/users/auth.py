from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError, decode
from sqlmodel import select

from database import AsyncSessionDep

from .models import User
from .schema import SessionSchema

bearer = HTTPBearer()

SECRET_KEY = 'your-secret-key'
ALGORITHM = 'HS256'


async def user_auth(
    session: AsyncSessionDep, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
):
    try:
        payload = decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None

    try:
        user_session = SessionSchema.model_validate(payload)
    except Exception:
        return None

    user = (await session.execute(select(User).where(User.id == user_session.user_id))).scalar_one()
    return user


async def admin(
    session: AsyncSessionDep, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
):
    try:
        payload = decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None

    try:
        user_session = SessionSchema.model_validate(payload)
    except Exception:
        return None

    if user_session.role != 'admin':
        return None

    user = (await session.execute(select(User).where(User.id == user_session.user_id))).scalar_one()
    return user


async def teacher(
    session: AsyncSessionDep, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
):
    try:
        payload = decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None

    try:
        user_session = SessionSchema.model_validate(payload)
    except Exception:
        return None

    if user_session.role != 'teacher':
        return None

    user = (await session.execute(select(User).where(User.id == user_session.user_id))).scalar_one()
    return user


async def student(
    session: AsyncSessionDep, credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
):
    try:
        payload = decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except PyJWTError:
        return None

    try:
        user_session = SessionSchema.model_validate(payload)
    except Exception:
        return None

    if user_session.role != 'student':
        return None
