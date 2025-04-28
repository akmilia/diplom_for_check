from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from typing import Any, Annotated
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/login",
    scheme_name="user_oauth2"
)

ALGORITHM = "HS256"
SECRET_KEY = "ваш-секрет-ключ"

TokenPayload = dict[str, Any]

def create_tokens(user_id: int, role: str) -> dict[str, str]:
    access_payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)

    refresh_payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    return {"access_token": access_token, "refresh_token": refresh_token}

def encode(data: dict[str, Any], key: str, algorithm: str) -> str:
    return jwt.encode(data, key, algorithm=algorithm)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if (user_id := payload.get("user_id")) is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if (role := payload.get("role")) is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return role
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def teacher_required(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
    if user.get("roles_idroles") != 2:
        raise HTTPException(403, "Teacher access required")
    return user

def student_required(user: Annotated[TokenPayload, Depends(get_current_user)]) -> TokenPayload:
    if user.get("roles_idroles") != 3:
        raise HTTPException(403, "Student access required")
    return user

# from datetime import datetime, timedelta, timezone
# from fastapi import Depends, HTTPException, status
# from typing import Any, Annotated, Optional  # type: ignore
# from jose import jwt, JWTError
# from fastapi.security import OAuth2PasswordBearer

# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="/api/login",
#     scheme_name="user_oauth2"
# )



# ALGORITHM = "HS256"
# SECRET_KEY = "ваш-секрет-ключ"

# TokenPayload = dict[str, Any]

# def create_access_token(data: dict[str, Any]) -> str:
#     to_encode = data.copy()
#     expire = datetime.now(timezone.utc) + timedelta(minutes=15)
#     to_encode.update({"exp": expire.isoformat()})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# def encode(data: dict[str, Any], key: str, algorithm: str) -> str:
#     return jwt.encode(data, key, algorithm=algorithm)

# async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenPayload:
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")

# async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         user_id: Optional[int] = payload.get("user_id") # type: ignore
#         if user_id is None:
#             raise credentials_exception
#         return user_id
#     except JWTError:
#         raise credentials_exception

# async def get_current_user_role(token: str = Depends(oauth2_scheme)) -> str:
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         role: Optional[str] = payload.get("role") # type: ignore
#         if role is None:
#             raise credentials_exception
#         return role
#     except JWTError:
#         raise credentials_exception

# def teacher_required(user: Annotated[TokenPayload, Depends(get_current_user)]):
#     if user.get("roles_idroles") != 2:
#         raise HTTPException(403, "Teacher access required")
#     return user

# def student_required(user: Annotated[TokenPayload, Depends(get_current_user)]):
#     if user.get("roles_idroles") != 3:
#         raise HTTPException(403, "Student access required")
#     return user;