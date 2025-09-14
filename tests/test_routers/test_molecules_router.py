import os
import sys
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.app.dependencies import get_db
from src.app.main import app
from src.app.models.molecule import Base, Molecule

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
            CREATE OR REPLACE FUNCTION update_morgan_fingerprint()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.morgan_fingerprint = morganbv_fp(mol_from_smiles(NEW.smiles::cstring));
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
            CREATE TRIGGER update_morgan_fingerprint_trigger
            BEFORE INSERT OR UPDATE ON molecules
            FOR EACH ROW EXECUTE FUNCTION update_morgan_fingerprint();
            """
      )
    )
    connection.commit()

  db = TestingSessionLocal()
  try:
    # Add test data
    mol1 = Molecule(
      id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
      inchi="inchi1",
      inchikey="inchikey1",
      smiles="CCO",
      molecular_weight=46.07,
      chemical_formula="C2H6O",
      logp=-0.31,
      tpsa=20.23,
      h_bond_donors=1,
      h_bond_acceptors=1,
      rotatable_bonds=0,
    )
    mol2 = Molecule(
      id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
      inchi="inchi2",
      inchikey="inchikey2",
      smiles="CCC",
      molecular_weight=44.1,
      chemical_formula="C3H8",
      logp=1.4,
      tpsa=0.0,
      h_bond_donors=0,
      h_bond_acceptors=0,
      rotatable_bonds=1,
    )
    mol3 = Molecule(
      id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
      inchi="inchi3",
      inchikey="inchikey3",
      smiles="CCCC",
      molecular_weight=58.12,
      chemical_formula="C4H10",
      logp=2.0,
      tpsa=0.0,
      h_bond_donors=0,
      h_bond_acceptors=0,
      rotatable_bonds=2,
    )
    db.add_all([mol1, mol2, mol3])
    db.commit()
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


def test_search_molecules_no_filters(client):
  response = client.get("/api/v1/search")
  assert response.status_code == 200
  data = response.json()
  assert len(data) == 3


def test_search_molecules_with_min_mol_weight(client):
  response = client.get("/api/v1/search?min_mol_weight=50")
  assert response.status_code == 200
  data = response.json()
  assert len(data) == 1
  assert data[0]["smiles"] == "CCCC"


def test_search_molecules_with_max_mol_weight(client):
  response = client.get("/api/v1/search?max_mol_weight=45")
  assert response.status_code == 200
  data = response.json()
  assert len(data) == 1
  assert data[0]["smiles"] == "CCC"


def test_search_molecules_with_min_and_max_mol_weight(client):
  response = client.get("/api/v1/search?min_mol_weight=45&max_mol_weight=50")
  assert response.status_code == 200
  data = response.json()
  assert len(data) == 1
  assert data[0]["smiles"] == "CCO"


def test_find_similar_molecules(client):
  response = client.post("/api/v1/search/similar", json={"smiles": "CCO", "min_similarity": 0.1})
  assert response.status_code == 200
  data = response.json()
  assert len(data) > 0
  assert data[0]["smiles"] == "CCO"
  assert "similarity_score" in data[0]
  assert data[0]["similarity_score"] == 1.0
