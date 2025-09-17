from typing import TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from rdkit import Chem, DataStructs
from sqlalchemy import REAL, Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base

from ..database_types import RDKitBfpType, RDKitMolType

Base = declarative_base()


class Molecule(Base):
  __tablename__ = "molecules"

  id = Column(PG_UUID(as_uuid=True), primary_key=True)
  inchi = Column(String, unique=True, nullable=False)
  inchikey = Column(String(27), unique=True, nullable=False)
  smiles = Column(String, nullable=False)
  mol = Column(RDKitMolType, nullable=True)
  molecular_weight = Column(REAL, nullable=False)
  chemical_formula = Column(String(255), nullable=False)
  logp = Column(REAL, nullable=False)
  tpsa = Column(REAL, nullable=False)
  h_bond_donors = Column(Integer, nullable=False)
  h_bond_acceptors = Column(Integer, nullable=False)
  rotatable_bonds = Column(Integer, nullable=False)
  morgan_fingerprint = Column(RDKitBfpType, nullable=False)


class MoleculeCreate(BaseModel):
  smiles: str


class MoleculeDict(TypedDict):
  id: UUID
  inchi: str
  inchikey: str
  smiles: str
  mol: Chem.Mol
  molecular_weight: float
  chemical_formula: str
  logp: float
  tpsa: float
  h_bond_donors: int
  h_bond_acceptors: int
  rotatable_bonds: int
  morgan_fingerprint: DataStructs.ExplicitBitVect  # ty: ignore[unresolved-attribute]


class MoleculeOut(BaseModel):
  id: UUID
  inchi: str
  inchikey: str
  smiles: str
  molecular_weight: float
  chemical_formula: str
  logp: float
  tpsa: float
  h_bond_donors: int
  h_bond_acceptors: int
  rotatable_bonds: int

  model_config = ConfigDict(from_attributes=True)


class MoleculeWithSimilarity(MoleculeOut):
  similarity_score: float


class SimilaritySearchResults(BaseModel):
  cache_hit: bool
  results: list[MoleculeWithSimilarity]
