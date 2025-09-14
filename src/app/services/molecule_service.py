from sqlalchemy.orm import Session

from ..repositories.molecule_repository import MoleculeRepository


class MoleculeService:
  def __init__(self, db: Session):
    self.repository = MoleculeRepository(db)

  def search_molecules(self, min_mol_weight: float = None, max_mol_weight: float = None):
    return self.repository.search(min_mol_weight, max_mol_weight)

  def find_similar_molecules(self, smiles: str, min_similarity: float = 0.7):
    return self.repository.find_similar(smiles, min_similarity)
