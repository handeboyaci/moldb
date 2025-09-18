import pytest
from alembic.config import Config
from fakeredis import FakeStrictRedis
from fastapi.testclient import TestClient
from rq import Queue
from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

import src.app.decorators
import src.app.services.cache_service
from alembic import command
from src.app.config import settings
from src.app.dependencies import db_session_context
from src.app.dependencies import get_db
from src.app.dependencies import get_redis_queue
from src.app.main import app

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db:5432/chemstructdb_test"


@pytest.fixture(scope="session")
def db_engine():
  """
  Creates a SQLAlchemy engine for the test session.
  """
  # Connect to the default postgres database to create the test database
  default_db_url = "postgresql://user:password@db:5432/postgres"
  default_engine = create_engine(default_db_url)
  with default_engine.connect() as connection:
    connection.execute(text("COMMIT"))
    # Check if the database exists
    result = connection.execute(
      text("SELECT 1 FROM pg_database WHERE datname = 'chemstructdb_test'")
    )
    if result.scalar() != 1:
      # Create the database if it doesn't exist
      connection.execute(text("CREATE DATABASE chemstructdb_test"))
    connection.commit()

  # Now, connect to the test database
  settings.DATABASE_URL = SQLALCHEMY_DATABASE_URL
  engine = create_engine(settings.DATABASE_URL)

  with engine.connect() as connection:
    connection.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS rdkit;"))
    connection.execute(text("SET rdkit.morgan_fp_size = 2048"))
    connection.commit()

  alembic_cfg = Config("alembic.ini")
  alembic_cfg.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))
  command.upgrade(alembic_cfg, "head")

  yield engine

  # Drop the test database after the test session
  default_db_url = "postgresql://user:password@db:5432/postgres"
  default_engine = create_engine(default_db_url)
  with default_engine.connect() as connection:
    connection.execute(text("COMMIT"))
    connection.execute(
      text(
        "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE"
        " pg_stat_activity.datname = 'chemstructdb_test' AND pid <> pg_backend_pid();"
      )
    )
    connection.execute(text("DROP DATABASE chemstructdb_test"))
    connection.commit()


@pytest.fixture(scope="function")
def db_session(db_engine, monkeypatch):
  """
  Yields a SQLAlchemy session wrapped in a transaction.
  Rolls back the transaction after the test is completed.
  """
  connection = db_engine.connect()
  transaction = connection.begin()
  Session = sessionmaker(bind=connection)
  session = Session()

  # Monkeypatch the commit method to prevent commits during tests
  monkeypatch.setattr(session, "commit", session.flush)

  yield session

  session.close()
  transaction.rollback()
  connection.close()


@pytest.fixture(scope="function")
def context_aware_task_queue(db_session):
  """
  Creates a synchronous RQ queue for testing that sets the db_session_context
  before executing a task. This ensures that tasks executed synchronously
  during tests use the correct transactional database session.
  """
  # Use a fake redis for the test queue
  fake_redis = FakeStrictRedis()
  queue = Queue(is_async=False, connection=fake_redis)

  # Store the original enqueue method
  original_enqueue = queue.enqueue

  def enqueue_with_context(f, *args, **kwargs):
    # Set the db session in the context variable for the duration of the task
    token = db_session_context.set(db_session)
    try:
      # Call the original enqueue method, which will execute the job synchronously
      return original_enqueue(f, *args, **kwargs)
    finally:
      # Reset the context variable
      db_session_context.reset(token)

  # Monkeypatch the queue's enqueue method
  queue.enqueue = enqueue_with_context

  yield queue


@pytest.fixture(scope="function")
def client(db_session, context_aware_task_queue, monkeypatch):
  """
  Provides a FastAPI TestClient with the database and task queue dependencies
  overridden for testing.
  """
  settings.TESTING = True

  def override_get_db():
    yield db_session

  def override_get_redis_queue():
    yield context_aware_task_queue

  app.dependency_overrides[get_db] = override_get_db
  app.dependency_overrides[get_redis_queue] = override_get_redis_queue

  # Patch the globally imported task_queue in the decorators module
  monkeypatch.setattr(src.app.decorators, "task_queue", context_aware_task_queue)

  # Patch the globally created redis client in the cache_service module
  monkeypatch.setattr(
    src.app.services.cache_service,
    "_redis_client",
    context_aware_task_queue.connection,
  )

  with TestClient(app) as c:
    yield c

  del app.dependency_overrides[get_db]
  del app.dependency_overrides[get_redis_queue]
