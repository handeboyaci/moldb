import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.app.models.molecule import Base, Molecule
from src.app.repositories.molecule_repository import MoleculeRepository


@pytest.fixture(scope="function")
def db():
  engine = create_engine("postgresql://user:password@db:5432/chemstructdb_test")
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

  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def repository(db):
  return MoleculeRepository(db)


def test_search_no_filters(repository, db):
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
  db.add_all([mol1, mol2])
  db.commit()

  molecules = repository.search()
  assert len(molecules) == 2


def test_search_with_min_mol_weight(repository, db):
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
  db.add_all([mol1, mol2])
  db.commit()
  molecules = repository.search(min_mol_weight=45)
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"


def test_search_with_max_mol_weight(repository, db):
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
  db.add_all([mol1, mol2])
  db.commit()
  molecules = repository.search(max_mol_weight=45)
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCC"


def test_find_similar(repository, db):
  # Add test data
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles="CCO",  # Ethanol
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
    smiles="CCN",  # Ethylamine
    molecular_weight=45.08,
    chemical_formula="C2H7N",
    logp=0.03,
    tpsa=26.02,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=1,
  )
  mol3 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
    inchi="inchi3",
    inchikey="inchikey3",
    smiles="C1CCCCC1",  # Cyclohexane
    molecular_weight=84.16,
    chemical_formula="C6H12",
    logp=3.44,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=0,
  )
  db.add_all([mol1, mol2, mol3])
  db.commit()

  # Search for molecules similar to Ethanol
  similar_molecules = repository.find_similar(smiles="CCO", min_similarity=0.1)

  assert len(similar_molecules) > 0
  # The most similar molecule should be ethanol itself
  assert similar_molecules[0].smiles == "CCO"
  assert hasattr(similar_molecules[0], "similarity_score")
  # The similarity of a molecule with itself is 1.0
  assert similar_molecules[0].similarity_score == 1.0


def test_substructure_search(repository, db):
  # Add test data
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles="CCO",  # Ethanol
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
    smiles="CCN",  # Ethylamine
    molecular_weight=45.08,
    chemical_formula="C2H7N",
    logp=0.03,
    tpsa=26.02,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=1,
  )
  mol3 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
    inchi="inchi3",
    inchikey="inchikey3",
    smiles="C1CCCCC1",  # Cyclohexane
    molecular_weight=84.16,
    chemical_formula="C6H12",
    logp=3.44,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=0,
  )
  db.add_all([mol1, mol2, mol3])
  db.commit()

  # Search for molecules containing the 'CC' substructure
  results = repository.substructure_search(smiles="CC")

  assert len(results) == 3
  assert "CCO" in [m.smiles for m in results]
  assert "CCN" in [m.smiles for m in results]
