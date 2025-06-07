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
        "exp": int(access_exp.timestamp())
    }
    refresh_payload = {
        "user_id": user_id,
        "exp": int(refresh_exp.timestamp())
    }

    return BearerSchema(
        access_token=jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM),
        refresh_token=jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM),
        token_type="bearer",
        user_id=user_id,
        role=role,
        expires_in=15 * 60,
        expires_at=access_exp
    )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> BearerSchema:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        role = payload.get("role")
        exp = payload.get("exp")
        if user_id is None or role is None or exp is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Собираем BearerSchema с фиктивными токенами, т.к. access_token/refresh_token в payload нет
        return BearerSchema(
            access_token=token,              # просто возвращаем текущий токен
            refresh_token="",                # refresh_token тут не нужен
            token_type="bearer",
            user_id=user_id,
            role=role,
            expires_in=int(exp - datetime.now(timezone.utc).timestamp()),
            expires_at=datetime.fromtimestamp(exp, tz=timezone.utc)
        )
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    user = await get_current_user(token)
    return user.user_id

async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    user = await get_current_user(token)
    return user.role

def teacher_required(user: Annotated[BearerSchema, Depends(get_current_user)]) -> BearerSchema:
    if user.role != "Преподаватель":
        raise HTTPException(403, "Teacher access required")
    return user

def student_required(user: Annotated[BearerSchema, Depends(get_current_user)]) -> BearerSchema:
    if user.role != "Ученик":
        raise HTTPException(403, "Student access required")
    return user
