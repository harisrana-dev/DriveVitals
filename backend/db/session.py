import os

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.base import Base


def _dsn() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError(
            "POSTGRES_PASSWORD environment variable is not set. "
            "Copy .env.example to .env and configure your database credentials."
        )
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "drivevitals_dev")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


engine = create_async_engine(_dsn(), echo=False, pool_pre_ping=True)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_db() -> None:
    await engine.dispose()
