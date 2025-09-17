from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.app.decorators import asynchronous_task
from src.worker.tasks import (
  create_molecule_task,
  find_similar_molecules_task,
  ingest_file_job,
  search_molecules_task,
  substructure_search_task,
)

from .. import dependencies
from ..models.molecule import (
  MoleculeCreate,
  MoleculeOut,
  SimilaritySearchResults,
)

router = APIRouter()


class IngestRequest(BaseModel):
  file_path: str


class SimilaritySearchRequest(BaseModel):
  smiles: str
  min_similarity: float = 0.7
  force_recompute: bool = False


class SubstructureSearchRequest(BaseModel):
  smiles: str


@router.post("/ingest")
@asynchronous_task
def ingest_molecules(request: IngestRequest, sync: bool = False, db: Session = Depends(dependencies.get_db)):
  return ingest_file_job, request.file_path


@router.post("/molecule", response_model=MoleculeOut)
@asynchronous_task
def create_molecule(request: MoleculeCreate, sync: bool = False, db: Session = Depends(dependencies.get_db)):
  # The actual logic is now in create_molecule_task
  # The decorator will enqueue this task.
  return create_molecule_task, request.smiles


@router.get("/search", response_model=list[MoleculeOut])
@asynchronous_task
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
  sync: bool = False,
  db: Session = Depends(dependencies.get_db),
):
  search_params = {
    "min_mol_weight": min_mol_weight,
    "max_mol_weight": max_mol_weight,
    "min_logp": min_logp,
    "max_logp": max_logp,
    "min_tpsa": min_tpsa,
    "max_tpsa": max_tpsa,
    "min_h_bond_donors": min_h_bond_donors,
    "max_h_bond_donors": max_h_bond_donors,
    "min_h_bond_acceptors": min_h_bond_acceptors,
    "max_h_bond_acceptors": max_h_bond_acceptors,
    "min_rotatable_bonds": min_rotatable_bonds,
    "max_rotatable_bonds": max_rotatable_bonds,
    "inchi": inchi,
    "inchikey": inchikey,
    "smiles": smiles,
    "chemical_formula": chemical_formula,
  }
  return search_molecules_task, search_params


@router.post("/search/similar", response_model=SimilaritySearchResults)
@asynchronous_task
def find_similar_molecules(
  request: SimilaritySearchRequest, sync: bool = False, db: Session = Depends(dependencies.get_db)
):
  return find_similar_molecules_task, request.smiles, request.min_similarity, request.force_recompute


@router.post("/search/substructure", response_model=list[MoleculeOut])
@asynchronous_task
def substructure_search(
  request: SubstructureSearchRequest, sync: bool = False, db: Session = Depends(dependencies.get_db)
):
  return substructure_search_task, request.smiles
