from concurrent.futures import ProcessPoolExecutor
from uuid import uuid4

from rdkit import Chem
from rdkit.Chem import (
  Descriptors,
  MolFromSmiles,
  MolToInchi,
  MolToInchiKey,
  rdFingerprintGenerator,
  rdMolDescriptors,
)
from sqlalchemy.orm import Session

from ..models.molecule import MoleculeDict
from ..repositories.molecule_repository import MoleculeRepository
from .cache_service import get_redis_client

# FingerprintGenerator singleton.
_fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)


def _process_smiles(smiles: str) -> tuple[MoleculeDict, str] | None:
  """
  Helper function to process a single SMILES string.
  This function is designed to be run in a separate process.
  """
  smiles = smiles.strip()
  if not smiles:
    return None
  try:
    mol = MolFromSmiles(smiles)
    if mol is None:
      raise ValueError("Invalid SMILES string")

    morgan_fingerprint = _fpgen.GetFingerprint(mol)
    inchikey = MolToInchiKey(mol)

    molecule_data: MoleculeDict = {
      "id": uuid4(),
      "inchi": MolToInchi(mol),
      "inchikey": inchikey,
      "smiles": smiles,
      "mol": mol,
      "molecular_weight": Descriptors.MolWt(mol),
      "chemical_formula": rdMolDescriptors.CalcMolFormula(mol),
      "logp": Descriptors.MolLogP(mol),  # ty: ignore[unresolved-attribute]
      "tpsa": Descriptors.TPSA(mol),  # ty: ignore[unresolved-attribute]
      "h_bond_donors": Descriptors.NumHDonors(mol),  # ty: ignore[unresolved-attribute]
      "h_bond_acceptors": Descriptors.NumHAcceptors(mol),  # ty: ignore[unresolved-attribute]
      "rotatable_bonds": Descriptors.NumRotatableBonds(mol),  # ty: ignore[unresolved-attribute]
      "morgan_fingerprint": morgan_fingerprint,
    }
    return molecule_data, inchikey
  except Exception:
    return None


class MoleculeService:
  def __init__(self, db: Session):
    self.repository = MoleculeRepository(db, get_redis_client())
    global _fpgen
    if _fpgen is None:
      _fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

  def create_molecule(self, smiles: str):
    mol = MolFromSmiles(smiles)
    if mol is None:
      raise ValueError("Invalid SMILES string")

    inchikey = MolToInchiKey(mol)

    # First, check if the molecule already exists.
    existing_molecule = self.repository.find_by_inchikey(inchikey)
    if existing_molecule:
      return existing_molecule

    # If it doesn't exist, create it.
    molecule_data: MoleculeDict = {
      "id": uuid4(),
      "inchi": MolToInchi(mol),
      "inchikey": inchikey,
      "smiles": smiles,
      "mol": mol,
      "molecular_weight": Descriptors.MolWt(mol),
      "chemical_formula": Chem.rdMolDescriptors.CalcMolFormula(mol),  # ty: ignore[unresolved-attribute]
      "logp": Descriptors.MolLogP(mol),  # ty: ignore[unresolved-attribute]
      "tpsa": Descriptors.TPSA(mol),  # ty: ignore[unresolved-attribute]
      "h_bond_donors": Descriptors.NumHDonors(mol),  # ty: ignore[unresolved-attribute]
      "h_bond_acceptors": Descriptors.NumHAcceptors(mol),  # ty: ignore[unresolved-attribute]
      "rotatable_bonds": Descriptors.NumRotatableBonds(mol),  # ty: ignore[unresolved-attribute]
      "morgan_fingerprint": _fpgen.GetFingerprint(mol),
    }

    return self.repository.create_molecule(molecule_data)

  def search_molecules(
    self,
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
    skip: int = 0,
    limit: int = 100,
  ):
    return self.repository.search(
      min_mol_weight=min_mol_weight,
      max_mol_weight=max_mol_weight,
      min_logp=min_logp,
      max_logp=max_logp,
      min_tpsa=min_tpsa,
      max_tpsa=max_tpsa,
      min_h_bond_donors=min_h_bond_donors,
      max_h_bond_donors=max_h_bond_donors,
      min_h_bond_acceptors=min_h_bond_acceptors,
      max_h_bond_acceptors=max_h_bond_acceptors,
      min_rotatable_bonds=min_rotatable_bonds,
      max_rotatable_bonds=max_rotatable_bonds,
      inchi=inchi,
      inchikey=inchikey,
      smiles=smiles,
      chemical_formula=chemical_formula,
      skip=skip,
      limit=limit,
    )

  def find_similar_molecules(
    self,
    smiles: str,
    min_similarity: float = 0.7,
    force_recompute: bool = False,
  ):
    return self.repository.find_similar(smiles, min_similarity, force_recompute)

  def substructure_search(self, smiles: str, skip: int = 0, limit: int = 100):
    return self.repository.substructure_search(smiles, skip=skip, limit=limit)

  def create_molecules_from_smiles(self, smiles_list: list[str], starting_line: int):
    molecules_to_create = []
    errors = []
    skipped_count = 0

    with ProcessPoolExecutor() as executor:
      results = executor.map(_process_smiles, smiles_list)

    for i, result in enumerate(results):
      if result:
        molecule_data, inchikey = result
        existing_molecule = self.repository.find_by_inchikey(inchikey)
        if existing_molecule:
          skipped_count += 1
        else:
          molecules_to_create.append(molecule_data)
      else:
        errors.append(
          {
            "line_number": starting_line + i,
            "smiles": smiles_list[i],
            "error": "Invalid SMILES or processing error",
          }
        )

    if molecules_to_create:
      self.repository.bulk_insert_molecules(molecules_to_create)

    return {
      "successfully_ingested": len(molecules_to_create),
      "failed_count": len(errors),
      "skipped_count": skipped_count,
      "errors": errors,
    }
