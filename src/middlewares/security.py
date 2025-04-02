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


# class SecurityMiddleware:
#     def __init__(self, app: ASGIApp):
#         self.app = app
#         self.logger = getLogger(__name__)

#     async def __call__(self, scope: Scope, receive: Receive, send: Send):
#         if scope['type'] != 'http':
#             return await self.app(scope, receive, send)

#         async def send_wrapper(message: Message) -> None:
#             if message['type'] == 'http.response.start':
#                 message['headers'] = message['headers'] + [
#                     (b'Strict-Transport-Security', b'max-age=63072000; includeSubDomains'),
#                     (b'X-Frame-Options', b'DENY'),
#                     (b'X-Content-Type-Options', b'nosniff'),
#                     (b'X-XSS-Protection', b'1; mode=block'),
#                 ]

#             await send(message)

#         return await self.app(scope, receive, send_wrapper)
