import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.app.dependencies import get_db
from src.app.main import app
from src.app.models.molecule import Base

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db:5432/chemstructdb_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
  engine = create_engine(SQLALCHEMY_DATABASE_URL)
  with engine.connect() as connection:
    connection.execute(text("CREATE EXTENSION IF NOT EXISTS rdkit"))
    connection.execute(
      text(
        """
            CREATE OR REPLACE FUNCTION update_molecule_data()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.mol = mol_from_smiles(NEW.smiles::cstring);
                NEW.morgan_fingerprint = morganbv_fp(NEW.mol);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """
      )
    )
    connection.commit()

  Base.metadata.create_all(bind=engine)
  with engine.connect() as connection:
    connection.execute(
      text(
        """
            CREATE TRIGGER update_molecule_data_trigger
            BEFORE INSERT OR UPDATE ON molecules
            FOR EACH ROW EXECUTE FUNCTION update_molecule_data();
            """
      )
    )
    connection.commit()

  db = TestingSessionLocal()
  try:
    yield db
  finally:
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
  def override_get_db():
    yield test_db

  app.dependency_overrides[get_db] = override_get_db
  with TestClient(app) as c:
    yield c
  del app.dependency_overrides[get_db]


def test_create_molecule_success(client):
  response = client.post("/api/v1/molecules", json={"smiles": "CCO"})
  assert response.status_code == 200
  data = response.json()
  assert "id" in data
  assert isinstance(data["id"], str)


def test_create_molecule_invalid_smiles(client):
  response = client.post("/api/v1/molecules", json={"smiles": "invalid-smiles"})
  assert response.status_code == 422  # Unprocessable Entity for validation errors
  data = response.json()
  assert "detail" in data


def test_create_molecule_missing_smiles(client):
  response = client.post("/api/v1/molecules", json={})
  assert response.status_code == 422  # Unprocessable Entity for validation errors
  data = response.json()
  assert "detail" in data
