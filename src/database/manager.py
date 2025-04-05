from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator # type: ignore
from typing import AsyncGenerator, Any, Generator # type: ignore
from sqlalchemy.ext.asyncio import (
    AsyncSession, 
    create_async_engine, 
    async_sessionmaker
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

class DBManager:
    def __init__(self, database_url: str) -> None:
        # Сохраняем оригинальный URL для синхронных подключений
        self.sync_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # Модифицируем URL для асинхронных подключений
        if not database_url.startswith("postgresql+asyncpg://"):
            if database_url.startswith("postgresql://"):
                database_url = database_url.replace(
                    "postgresql://", 
                    "postgresql+asyncpg://", 
                    1
                )
            else:
                raise ValueError(
                    "Invalid database URL. Required format: "
                    "postgresql+asyncpg://user:password@host/dbname or "
                    "postgresql://user:password@host/dbname"
                )

        # Асинхронный движок для приложения
        self.async_engine = create_async_engine(
            database_url,
            connect_args={"server_settings": {"jit": "off"}},
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            echo=True
        )
        
        # Синхронный движок для миграций
        self.sync_engine = create_engine(
            self.sync_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            echo=True
        )

        # Асинхронная фабрика сессий
        self.async_session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )

        # Синхронная фабрика сессий
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine,
            expire_on_commit=False,
            autoflush=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, Any]:
        """Асинхронный контекстный менеджер для приложения"""
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    @contextmanager
    def sync_session(self) -> Generator[Session, Any, None]:
        """Синхронный контекстный менеджер для миграций"""
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @property
    def sync_connection_url(self) -> str:
        """Возвращает синхронный URL для Alembic"""
        return self.sync_url

# Инициализация с async URL, но сохраняем sync версию
db_manager = DBManager("postgresql+asyncpg://postgres:2006@localhost:5432/diplom_school")

async def get_session() -> AsyncIterator[AsyncSession]:  # Измененная строка
    async with db_manager.session() as session:
        yield session