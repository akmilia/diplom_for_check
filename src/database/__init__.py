from contextlib import asynccontextmanager
from logging import getLogger
import logging
from typing import Annotated

from alembic.command import upgrade
from alembic.config import Config
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from apps.users.models import Users, Schedule, Subjects, Types, Roles, Groups, t_usersshow, t_scheduleshow, t_subjectsshow, Attendance, BilNebil, TypesSubjects, Cabinets, Base
from core.config import settings
from database.manager import DBManager, db_manager

Base.metadata.reflect

logger = getLogger(__name__)

db_manager = DBManager(settings.DATABASE_URL)
# SyncSessionDep = Annotated[Session, Depends(db_manager.sync_session)]
AsyncSessionDep = Annotated[AsyncSession, Depends(db_manager.session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from alembic.config import Config
        from alembic import command
        import asyncio
        
        alembic_cfg = Config("alembic.ini")
        def run_migrations():
            command.upgrade(alembic_cfg, "head")
            
        await asyncio.to_thread(run_migrations)
        yield
    except Exception as e:
        logging.error(f"Migration error: {e}")
        raise