from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from typing import Annotated
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from apps.users.schema import BearerSchema

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/login",  
    scheme_name="user_oauth2"
)

SECRET_KEY = 'your-secret-key'
ALGORITHM = 'HS256'

def create_tokens(user_id: int, role: str) -> BearerSchema:
    access_exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    refresh_exp = datetime.now(timezone.utc) + timedelta(days=7)
    
    access_payload = {
        "user_id": user_id,
        "role": role,
        "exp": access_exp
    }
    refresh_payload = {
        "user_id": user_id,
        "exp": refresh_exp
    }
    
    return BearerSchema(
        access_token=jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM),
        refresh_token=jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM),
        token_type="bearer", 
        user_id=user_id,
        role=role,
        expires_in=1800,
        expires_at=access_exp
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> BearerSchema:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return BearerSchema(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    payload = await get_current_user(token)
    return payload.user_id

async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    payload = await get_current_user(token)
    return payload.role

def teacher_required(user: Annotated[BearerSchema, Depends(get_current_user)]) -> BearerSchema:
    if user.role != "Преподаватель":
        raise HTTPException(403, "Teacher access required")
    return user

def student_required(user: Annotated[BearerSchema, Depends(get_current_user)]) -> BearerSchema:
    if user.role != "Ученик":
        raise HTTPException(403, "Student access required")
    return user
