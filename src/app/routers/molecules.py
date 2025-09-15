from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import dependencies
from ..models.molecule import MoleculeCreate, MoleculeOut
from ..services.molecule_service import MoleculeService

router = APIRouter()


class SimilaritySearchRequest(BaseModel):
  smiles: str
  min_similarity: float = 0.7


class SubstructureSearchRequest(BaseModel):
  smiles: str


@router.post("/molecule", response_model=MoleculeOut)
def create_molecule(request: MoleculeCreate, db: Session = Depends(dependencies.get_db)):
  print("HERE")
  service = MoleculeService(db)
  try:
    return service.create_molecule(request.smiles)
  except IntegrityError:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Molecule with this InChI already exists.")


@router.get("/search", response_model=list[MoleculeOut])
def search_molecules(
  min_mol_weight: float | None = None,
  max_mol_weight: float | None = None,
  min_logp: float | None = None,
  max_logp: float | None = None,
  min_tpsa: float | None = None,
  max_tpsa: float | None = None,
  min_h_bond_donors: int | None = None,
  max_h_bond_donors: int | None = None,
  min_h_bond_acceptors: int | None = None,
  max_h_bond_acceptors: int | None = None,
  min_rotatable_bonds: int | None = None,
  max_rotatable_bonds: int | None = None,
  inchi: str | None = None,
  inchikey: str | None = None,
  smiles: str | None = None,
  chemical_formula: str | None = None,
  db: Session = Depends(dependencies.get_db),
):
  service = MoleculeService(db)
  return service.search_molecules(
    min_mol_weight,
    max_mol_weight,
    min_logp,
    max_logp,
    min_tpsa,
    max_tpsa,
    min_h_bond_donors,
    max_h_bond_donors,
    min_h_bond_acceptors,
    max_h_bond_acceptors,
    min_rotatable_bonds,
    max_rotatable_bonds,
    inchi,
    inchikey,
    smiles,
    chemical_formula,
  )


@router.post("/search/similar", response_model=list[MoleculeOut])
def find_similar_molecules(request: SimilaritySearchRequest, db: Session = Depends(dependencies.get_db)):
  service = MoleculeService(db)
  return service.find_similar_molecules(request.smiles, request.min_similarity)


@router.post("/search/substructure", response_model=list[MoleculeOut])
def substructure_search(request: SubstructureSearchRequest, db: Session = Depends(dependencies.get_db)):
  service = MoleculeService(db)
  return service.substructure_search(request.smiles)
