import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from src.app.config import settings
from src.app.dependencies import get_db
from src.app.main import app


@pytest.fixture(scope="session")
def db_engine():
  """
  Creates a SQLAlchemy engine for the test session.
  """
  engine = create_engine(
    settings.DATABASE_URL,
  )

  with engine.connect() as connection:
    connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    connection.commit()

  alembic_cfg = Config("alembic.ini")
  alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
  command.upgrade(alembic_cfg, "head")

  yield engine


@pytest.fixture(scope="function")
def db_session(db_engine):
  """
  Yields a SQLAlchemy session wrapped in a transaction.
  Rolls back the transaction after the test is completed.
  """
  connection = db_engine.connect()
  transaction = connection.begin()
  Session = sessionmaker(bind=connection)
  session = Session()

  yield session

  session.close()
  transaction.rollback()
  connection.close()


@pytest.fixture(scope="function")
def client(db_session):
  """
  Provides a FastAPI TestClient with the database dependency
  overridden to use the transactional session.
  """
  settings.TESTING = True

  def override_get_db():
    yield db_session

  app.dependency_overrides[get_db] = override_get_db
  with TestClient(app) as c:
    yield c
  del app.dependency_overrides[get_db]
