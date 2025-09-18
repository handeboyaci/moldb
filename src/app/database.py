from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@lru_cache()
def get_engine(db_url: str):
  return create_engine(db_url)


@lru_cache()
def get_session_local(db_url: str):
  return sessionmaker(autocommit=False, autoflush=False, bind=get_engine(db_url))
