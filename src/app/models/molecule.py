
from sqlalchemy import Column, Integer, String, Float, REAL
from sqlalchemy.dialects.postgresql import UUID
from razi.rdkit_postgresql.types import Bfp
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class Molecule(Base):
    __tablename__ = "molecules"

    id = Column(UUID(as_uuid=True), primary_key=True)
    inchi = Column(String, unique=True, nullable=False)
    inchikey = Column(String(27), unique=True, nullable=False)
    smiles = Column(String, nullable=False)
    molecular_weight = Column(REAL, nullable=False)
    chemical_formula = Column(String(255), nullable=False)
    logp = Column(REAL, nullable=False)
    tpsa = Column(REAL, nullable=False)
    h_bond_donors = Column(Integer, nullable=False)
    h_bond_acceptors = Column(Integer, nullable=False)
    rotatable_bonds = Column(Integer, nullable=False)
    morgan_fingerprint = Column(Bfp, nullable=False)

class MoleculeCreate(BaseModel):
    smiles: str

class MoleculeInDB(MoleculeCreate):
    inchikey: str
    molecular_weight: float
    chemical_formula: str
    logp: float
    tpsa: float
    h_bond_donors: int
    h_bond_acceptors: int
    rotatable_bonds: int

    class Config:
        orm_mode = True
