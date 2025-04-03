from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from typing import  Any, Annotated
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login",  # Укажите ваш реальный эндпоинт для аутентификации
    scheme_name="user_oauth2"
)
# Конфигурация (вынесите в настройки если нужно)
ALGORITHM = "HS256"
SECRET_KEY = "ваш-секрет-ключ"  

TokenPayload = dict[str, Any]

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire.isoformat()})  # Преобразуем datetime в строку ISO
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def encode(data: dict[str, Any], key: str, algorithm: str) -> str:
    return jwt.encode(data, key, algorithm=algorithm)  

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def teacher_required(user: Annotated[TokenPayload, Depends(get_current_user)]):
    if user.get("roles_idroles") != 2:
        raise HTTPException(403, "Teacher access required")
    return user

def student_required(user: Annotated[TokenPayload, Depends(get_current_user)]):
    if user.get("roles_idroles") != 3:
        raise HTTPException(403, "Student access required")
    return user