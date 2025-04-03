from logging import getLogger
from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from .access_log_middleware import AccessLogMiddleware
from .security import teacher_required, student_required  # Импортируем зависимости для роутов

logger = getLogger(__name__)

def register_middlewares(app: FastAPI) -> FastAPI:
    """
    Регистрирует все middleware для приложения FastAPI.
    
    Args:
        app (FastAPI): Экземпляр FastAPI приложения
        
    Returns:
        FastAPI: Модифицированное приложение с middleware
    """
    # Middleware для сжатия ответов
    app.add_middleware(
        GZipMiddleware,
        minimum_size=1000,
        compresslevel=5
    )
    
    # Middleware для логгирования запросов
    app.add_middleware(AccessLogMiddleware)
    
    return app

# Экспортируем зависимости для использования в роутерах
__all__ = [
    'register_middlewares',
    'teacher_required',
    'student_required',
    'AccessLogMiddleware'
]