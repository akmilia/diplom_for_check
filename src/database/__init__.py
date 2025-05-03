from contextlib import asynccontextmanager
from logging import getLogger
import logging
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.models import Base, Users, Schedule, Subjects, Roles, BilNebil, Attendance, Cabinets, t_scheduleshow, t_subjects_with_types, t_subjectsshow, t_usersshow, Types
from core.config import settings
from database.manager import DBManager, db_manager

# Base.metadata.reflect

logger = getLogger(__name__)

db_manager = DBManager(settings.DATABASE_URL)
AsyncSessionDep = Annotated[AsyncSession, Depends(db_manager.session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # Создаем все таблицы при старте
        async with db_manager.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        yield
    except Exception as e:
        logging.error(f"Database error: {e}")
        raise

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     try:
#         from alembic.config import Config
#         from alembic import command
#         import asyncio
        
#         alembic_cfg = Config("alembic.ini")
#         def run_migrations():
#             command.upgrade(alembic_cfg, "head")
            
#         await asyncio.to_thread(run_migrations)
#         yield
#     except Exception as e:
#         logging.error(f"Migration error: {e}")
#         raise