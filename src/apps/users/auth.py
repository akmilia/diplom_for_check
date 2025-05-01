from typing import Annotated
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt  
from pydantic import ValidationError 
from sqlmodel import select
from database import AsyncSessionDep
from apps.users.models import Users
from apps.users.schema import BearerSchema

bearer = HTTPBearer()

SECRET_KEY = 'your-secret-key'
ALGORITHM = 'HS256'

async def user_auth(
    session: AsyncSessionDep, 
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
) -> BearerSchema:
    try:
        payload = jwt.decode(
            credentials.credentials, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        return BearerSchema(**payload)
    except (JWTError, ValidationError) as e:
        raise HTTPException(
            status_code=401, 
            detail=f"Invalid token: {str(e)}"
        )

async def teacher_required(
    session: AsyncSessionDep, 
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
) -> Users:
    try:
        token_payload = await user_auth(session, credentials)
        if token_payload.role != 'Преподаватель':
            raise HTTPException(403, "Teacher access required")
            
        user = (await session.execute(
            select(Users).where(Users.idusers == token_payload.user_id)
        )).scalar_one()
        
        return user
    except Exception as e:
        raise HTTPException(401, detail=str(e))

async def student_required(
    session: AsyncSessionDep, 
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)]
) -> Users:
    try:
        token_payload = await user_auth(session, credentials)
        if token_payload.role != 'Ученик':
            raise HTTPException(403, "Student access required")
            
        user = (await session.execute(
            select(Users).where(Users.idusers == token_payload.user_id)
        )).scalar_one()
        
        return user
    except Exception as e:
        raise HTTPException(401, detail=str(e))