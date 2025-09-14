from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.molecule import Molecule


class MoleculeRepository:
  def __init__(self, db: Session):
    self.db = db

  def search(self, min_mol_weight: float = None, max_mol_weight: float = None):
    query = self.db.query(Molecule)
    if min_mol_weight is not None:
      query = query.filter(Molecule.molecular_weight >= min_mol_weight)
    if max_mol_weight is not None:
      query = query.filter(Molecule.molecular_weight <= max_mol_weight)
    return query.all()

  def find_similar(self, smiles: str, min_similarity: float = 0.7):
    # Calculate the fingerprint for the input SMILES
    query_fp = func.morganbv_fp(func.mol_from_smiles(smiles), 2)

    # Perform the similarity search
    q = (
      self.db.query(
        Molecule,
        func.tanimoto_sml(Molecule.morgan_fingerprint, query_fp).label("similarity"),
      )
      .filter(func.tanimoto_sml(Molecule.morgan_fingerprint, query_fp) >= min_similarity)
      .order_by(func.tanimoto_sml(Molecule.morgan_fingerprint, query_fp).desc())
    )

    results = q.all()

    # The result is a list of (Molecule, similarity_score) tuples.
    # We need to add the similarity_score to each molecule object.
    output = []
    for molecule, similarity in results:
      molecule.similarity_score = similarity
      output.append(molecule)

    return output
