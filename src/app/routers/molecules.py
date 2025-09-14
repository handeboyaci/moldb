from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import dependencies
from ..services.molecule_service import MoleculeService

router = APIRouter()


class SimilaritySearchRequest(BaseModel):
  smiles: str
  min_similarity: float = 0.7


class SubstructureSearchRequest(BaseModel):
  smiles: str


@router.get("/search")
def search_molecules(
  min_mol_weight: float = None,
  max_mol_weight: float = None,
  db: Session = Depends(dependencies.get_db),
):
  service = MoleculeService(db)
  return service.search_molecules(min_mol_weight, max_mol_weight)


@router.post("/search/similar")
def find_similar_molecules(request: SimilaritySearchRequest, db: Session = Depends(dependencies.get_db)):
  service = MoleculeService(db)
  return service.find_similar_molecules(request.smiles, request.min_similarity)


@router.post("/search/substructure")
def substructure_search(request: SubstructureSearchRequest, db: Session = Depends(dependencies.get_db)):
  service = MoleculeService(db)
  return service.substructure_search(request.smiles)
