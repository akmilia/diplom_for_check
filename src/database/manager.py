from contextlib import asynccontextmanager, contextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import Session, StaticPool, create_engine 

class DBManager:
    sync_url = ''
    async_url = ''

    postgres_args = {
        'pool_size': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,
    }
    sqlite_args = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False},
    }

    def __init__(self, database_url: str):
        database_url_split = database_url.split('://')

        if database_url.startswith('sqlite://'):
            self.sync_url = f'sqlite://{database_url_split[1]}'
            self.async_url = f'sqlite+aiosqlite://{database_url_split[1]}'
            args = self.sqlite_args

        elif database_url.startswith('postgresql://'):
            self.sync_url = f'postgresql+asyncpg://{database_url_split[1]}'
            self.async_url = f'postgresql+asyncpg://{database_url_split[1]}'
            args = self.postgres_args

        else:
            raise ValueError(f'Invalid database URL: {database_url}')

        self.sync_engine = create_engine(self.sync_url, **args)
        self.async_engine = create_async_engine(self.async_url, **args)

        self.sync_test_engine = create_engine('sqlite:///test.db', **self.sqlite_args)
        self.async_test_engine = create_async_engine(
            'sqlite+aiosqlite:///test.db', **self.sqlite_args
        )

    def sync_session(self):
        with Session(self.sync_engine) as session:
            yield session

    def sync_test_session(self):
        with Session(self.sync_test_engine) as session:
            yield session

    async def async_session(self):
        async with AsyncSession(self.async_engine) as session:
            yield session

    async def async_test_session(self):
        async with AsyncSession(self.async_test_engine) as session:
            yield session

    @contextmanager
    def sync_context_session(self):
        with Session(self.sync_engine) as session:
            yield session

    @contextmanager
    def sync_context_test_session(self):
        with Session(self.sync_test_engine) as session:
            yield session

    @asynccontextmanager
    async def async_context_session(self):
        async with AsyncSession(self.async_engine) as session:
            yield session

    @asynccontextmanager
    async def async_context_test_session(self):
        async with AsyncSession(self.async_test_engine) as session:
            yield session


# from contextlib import asynccontextmanager, contextmanager

# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlmodel import Session, StaticPool, create_engine


# class DBManager:
#     sync_url = ''
#     async_url = ''

#     postgres_args = {
#         'pool_size': 10,
#         'max_overflow': 5,
#         'pool_timeout': 30,
#         'pool_recycle': 1800,
#     }
#     sqlite_args = {
#         'poolclass': StaticPool,
#         'connect_args': {'check_same_thread': False},
#     }

#     def __init__(self, database_url: str):
#         database_url_split = database_url.split('://')

#         if database_url.startswith('sqlite://'):
#             self.sync_url = f'sqlite://{database_url_split[1]}'
#             self.async_url = f'sqlite+aiosqlite://{database_url_split[1]}'
#             args = self.sqlite_args

#         elif database_url.startswith('postgresql://'):
#             self.sync_url = f'postgresql+psycopg://{database_url_split[1]}'
#             self.async_url = f'postgresql+asyncpg://{database_url_split[1]}'
#             args = self.postgres_args

#         else:
#             raise ValueError(f'Invalid database URL: {database_url}')

#         self.sync_engine = create_engine(self.sync_url, **args)
#         self.async_engine = create_async_engine(self.async_url, **args)

#         self.sync_test_engine = create_engine('sqlite:///test.db', **self.sqlite_args)
#         self.async_test_engine = create_async_engine(
#             'sqlite+aiosqlite:///test.db', **self.sqlite_args
#         )

#     def sync_session(self):
#         with Session(self.sync_engine) as session:
#             yield session

#     def sync_test_session(self):
#         with Session(self.sync_test_engine) as session:
#             yield session

#     async def async_session(self):
#         async with AsyncSession(self.async_engine) as session:
#             yield session

#     async def async_test_session(self):
#         async with AsyncSession(self.async_test_engine) as session:
#             yield session

#     @contextmanager
#     def sync_context_session(self):
#         with Session(self.sync_engine) as session:
#             yield session

#     @contextmanager
#     def sync_context_test_session(self):
#         with Session(self.sync_test_engine) as session:
#             yield session

#     @asynccontextmanager
#     async def async_context_session(self):
#         async with AsyncSession(self.async_engine) as session:
#             yield session

#     @asynccontextmanager
#     async def async_context_test_session(self):
#         async with AsyncSession(self.async_test_engine) as session:
#             yield session
