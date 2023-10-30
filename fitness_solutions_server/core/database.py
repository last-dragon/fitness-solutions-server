from typing import Annotated, AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import settings

async_engine = create_async_engine(url=settings.DATABASE_URL, future=True)
session_maker = async_sessionmaker(
    bind=async_engine,
    future=True,
    expire_on_commit=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    session = session_maker()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


DatabaseDependency = Annotated[AsyncSession, Depends(get_db)]

# TODO: sys:1: SAWarning: Object of type <Workout> not in session, add operation along 'User.workouts' will not proceed (This warning originated from the Session 'autoflush' process, which was invoked automatically in response to a user-initiated operation.)
