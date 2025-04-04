from logging import getLogger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import lifespan
from middlewares import register_middlewares 

from .config import settings
from .exceptions import register_exceptions
from .router import v1_router

logger = getLogger(__name__) 


origins = [
    "http://localhost:5173",  # URL вашего React приложения
    "http://127.0.0.1:5173",
    "https://localhost", 
    "http://localhost",
    "http://127.0.0.1",
] 

app = FastAPI( 
    version="1.0.0",
    debug=settings.DEBUG,
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    openapi_url='/v1/openapi.json' if settings.DEBUG else None,
    docs_url='/v1/docs' if settings.DEBUG else None,
    redoc_url='/v1/redoc' if settings.DEBUG else None,
    lifespan=lifespan
)


# Настройка CORS
app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    # allow_origins= origins,  # Разрешенные источники (ваша frontend)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешенные методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешенные заголовки
) 

app = register_middlewares(app)
app = register_exceptions(app)
app.include_router(v1_router)

