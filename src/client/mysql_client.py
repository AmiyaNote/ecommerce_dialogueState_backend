from sqlalchemy.ext.asyncio import (
    AsyncEngine, async_sessionmaker, AsyncSession, create_async_engine,
)

from conf.load_env import env_config

engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db_engine():
    global engine, session_factory
    engine = create_async_engine(env_config["DATABASE_URL"])
    session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def close_db_engine():
    await engine.dispose()


