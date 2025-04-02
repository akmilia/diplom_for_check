from datetime import datetime, timedelta
from jose import jwt

# Конфигурация (вынесите в настройки если нужно)
ALGORITHM = "HS256"
SECRET_KEY = "ваш-секрет-ключ"  # Замените на реальный ключ!

def create_access_token(data: dict): # type: ignore
    to_encode = data.copy() # type: ignore
    expire = datetime.utcnow() + timedelta(minutes=15) # type: ignore
    to_encode.update({"exp": expire})  # type: ignore
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # type: ignore 
def encode(data: dict, key: str, algorithm: str):
    return jwt.encode(data, key, algorithm=algorithm)
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
