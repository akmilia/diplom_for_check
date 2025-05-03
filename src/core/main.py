from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import lifespan
from middlewares import register_middlewares
from .config import settings
from .exceptions import register_exceptions
from apps.users.routers import router


app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version="1.0.0",
    openapi_url='/openapi.json',
    docs_url='/docs',
    redoc_url='/redoc',
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[
    #     "http://localhost:5173",
    #     "http://127.0.0.1:5173"
    # ],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
) 

# Регистрация дополнительных компонентов
app = register_middlewares(app)
app = register_exceptions(app)

# Подключение роутеров
app.include_router(router) 

import logging

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Уменьшаем логгирование SQLAlchemy
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)