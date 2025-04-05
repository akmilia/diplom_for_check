from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from typing import Any, Annotated, Optional  # type: ignore
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login",
    scheme_name="user_oauth2"
)

ALGORITHM = "HS256"
SECRET_KEY = "ваш-секрет-ключ"

TokenPayload = dict[str, Any]

def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire.isoformat()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def encode(data: dict[str, Any], key: str, algorithm: str) -> str:
    return jwt.encode(data, key, algorithm=algorithm)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("usersid") # type: ignore
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        role: Optional[str] = payload.get("role") # type: ignore
        if role is None:
            raise credentials_exception
        return role
    except JWTError:
        raise credentials_exception

def teacher_required(user: Annotated[TokenPayload, Depends(get_current_user)]):
    if user.get("roles_idroles") != 2:
        raise HTTPException(403, "Teacher access required")
    return user

def student_required(user: Annotated[TokenPayload, Depends(get_current_user)]):
    if user.get("roles_idroles") != 3:
        raise HTTPException(403, "Student access required")
    return user