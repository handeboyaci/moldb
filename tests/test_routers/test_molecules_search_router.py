import os
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))


SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db:5432/chemstructdb_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
  engine = create_engine(SQLALCHEMY_DATABASE_URL)
  with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS rdkit"))
    connection.commit()

  # Run Alembic migrations to set up the schema
  os.system("docker compose exec app alembic upgrade head")

  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
    # Downgrade Alembic migrations to clean up the schema
    os.system("docker compose exec app alembic downgrade base")
