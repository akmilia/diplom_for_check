from contextlib import asynccontextmanager
from logging import getLogger
from typing import Annotated

from alembic.command import upgrade
from alembic.config import Config
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session

from core.config import settings
from database.manager import DBManager

logger = getLogger(__name__)


db_manager = DBManager(settings.DATABASE_URL)
SyncSessionDep = Annotated[Session, Depends(db_manager.sync_session)]
AsyncSessionDep = Annotated[AsyncSession, Depends(db_manager.async_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'App Name: {settings.APP_NAME}')
    logger.info(f'App Description: {settings.APP_DESCRIPTION}')

    config = Config('alembic.ini')
    upgrade(config, 'head')

    yield
