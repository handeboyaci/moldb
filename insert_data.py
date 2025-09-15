import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.app.models.molecule import Base, Molecule

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@db:5432/chemstructdb"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

db = SessionLocal()
try:
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
        smiles="CCC",  # Propane
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
    print("Data inserted successfully.")
except Exception as e:
    db.rollback()
    print(f"Error inserting data: {e}")
finally:
    db.close()
