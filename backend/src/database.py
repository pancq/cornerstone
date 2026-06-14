from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# 判断是否为SQLite
is_sqlite = settings.database_url.startswith("sqlite")

# 异步引擎
if is_sqlite:
    async_engine = create_async_engine(
        settings.database_url, 
        echo=settings.debug,
        connect_args={"check_same_thread": False}
    )
else:
    async_engine = create_async_engine(settings.database_url, echo=settings.debug)

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 同步引擎（用于Alembic迁移）
if is_sqlite:
    sync_engine = create_engine(
        settings.database_url_sync, 
        echo=settings.debug,
        connect_args={"check_same_thread": False}
    )
else:
    sync_engine = create_engine(settings.database_url_sync, echo=settings.debug)

sync_session = sessionmaker(sync_engine, expire_on_commit=False)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session
