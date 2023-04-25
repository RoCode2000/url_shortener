from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from pydantic import BaseModel

SQLALCHEMY_DATABASE_URL = "sqlite:///./url_shortener.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Item(BaseModel):
    url: str
    url_base: str


Base = declarative_base()
