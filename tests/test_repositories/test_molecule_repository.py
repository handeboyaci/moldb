
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

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
        connection.commit()

    Base.metadata.create_all(bind=engine)
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
        morgan_fingerprint="0101",
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
        morgan_fingerprint="0101",
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
        morgan_fingerprint="0101",
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
        morgan_fingerprint="0101",
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
        morgan_fingerprint="0101",
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
        morgan_fingerprint="0101",
    )
    db.add_all([mol1, mol2])
    db.commit()
    molecules = repository.search(max_mol_weight=45)
    assert len(molecules) == 1
    assert molecules[0].smiles == "CCC"
