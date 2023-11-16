from sqlalchemy.ext.declarative import declarative_base

from app.models import PetType
from .config import settings

# SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL
# )
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

import os
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
# DATABASE_URL = os.environ.get("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = SessionLocal()
    try:
        pet_types = [PetType(type="Dog"), PetType(type="Cat")]
        session.add_all(pet_types)
        await session.commit()
    except Exception as e:
        await session.rollback()
    finally:
        await session.close()

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

