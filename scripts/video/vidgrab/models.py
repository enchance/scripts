import os, sys, sqlalchemy as sa
from pathlib import Path
from enum import StrEnum, auto
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date
from sqlmodel import SQLModel, Field, text
from sqlmodel.ext.asyncio.session import AsyncSession
from icecream import IceCreamDebugger
from dotenv import load_dotenv





ic = IceCreamDebugger(prefix='')
# path = Path(__file__).resolve().parent.parent.parent
# load_dotenv(dotenv_path=os.path.join(path, '.env'))

DATABASE_URL = os.environ.get('VIDGRAB_URL')
# SCRIPTS_URL = os.environ.get('SCRIPTS_URL')
# sys.path.append(SCRIPTS_URL)

engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)   # noqa
Base = declarative_base()


class Status(StrEnum):
    done = auto()
    pending = auto()
    incomplete = auto()
    pause = auto()
    error = auto()


class Whitelist(SQLModel, table=True):
    __tablename__ = 'app_whitelist'
    id: int | None = Field(primary_key=True, default=None)
    url: str = Field(unique=True, nullable=False)
    is_nsfw: bool = Field(default=False)


class Video(SQLModel, table=True):
    __tablename__ = 'app_video'
    id: int | None = Field(primary_key=True, default=None)
    url: str = Field(max_length=255)
    session: date = Field(sa_column=sa.Column(sa.Date))
    status: Status = Field(max_length=20)
    source: str | None = Field(max_length=90)
    created_at: datetime | None = Field(sa_column=sa.Column(sa.DateTime(timezone=True),
                                                            server_default=text('CURRENT_TIMESTAMP')))
    updated_at: datetime | None = Field(sa_column=sa.Column(sa.DateTime(timezone=True),
                                                            server_default=text('CURRENT_TIMESTAMP'),
                                                            server_onupdate=text('CURRENT_TIMESTAMP')))     # noqa

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
