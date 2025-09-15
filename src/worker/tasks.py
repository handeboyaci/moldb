from src.app import dependencies
from src.app.services.molecule_service import MoleculeService


def create_molecule_task(smiles: str):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.create_molecule(smiles)


def search_molecules_task(search_params: dict):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.search_molecules(**search_params)


def find_similar_molecules_task(smiles: str, min_similarity: float):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.find_similar_molecules(smiles, min_similarity)


def substructure_search_task(smiles: str):
  db = next(dependencies.get_db())
  service = MoleculeService(db)
  return service.substructure_search(smiles)
