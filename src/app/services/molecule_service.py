from uuid import uuid4

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors, MolFromSmiles, MolToInchi, MolToInchiKey
from sqlalchemy.orm import Session

from ..models.molecule import MoleculeInDB
from ..repositories.molecule_repository import MoleculeRepository


class MoleculeService:
  def __init__(self, db: Session):
    self.repository = MoleculeRepository(db)

  def create_molecule(self, smiles: str):
    print(f"Attempting to create molecule for SMILES: {smiles}")
    mol = MolFromSmiles(smiles)
    if mol is None:
      print(f"Invalid SMILES string: {smiles}")
      raise ValueError("Invalid SMILES string")

    print("SMILES converted to RDKit mol object.")
    inchi = MolToInchi(mol)
    inchikey = MolToInchiKey(mol)
    molecular_weight = Descriptors.MolWt(mol)
    chemical_formula = Chem.rdMolDescriptors.CalcMolFormula(mol)
    logp = Descriptors.MolLogP(mol)
    tpsa = Descriptors.TPSA(mol)
    h_bond_donors = Descriptors.NumHDonors(mol)
    h_bond_acceptors = Descriptors.NumHAcceptors(mol)
    rotatable_bonds = Descriptors.NumRotatableBonds(mol)
    morgan_fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
    print("Molecular properties and fingerprint calculated.")

    molecule_data = MoleculeInDB(
      id=uuid4(),
      inchi=inchi,
      inchikey=inchikey,
      smiles=smiles,
      mol=mol,
      molecular_weight=molecular_weight,
      chemical_formula=chemical_formula,
      logp=logp,
      tpsa=tpsa,
      h_bond_donors=h_bond_donors,
      h_bond_acceptors=h_bond_acceptors,
      rotatable_bonds=rotatable_bonds,
      morgan_fingerprint=morgan_fingerprint,
    )
    print("MoleculeInDB object created.")
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
  ):
    return self.repository.search(
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

  def find_similar_molecules(self, smiles: str, min_similarity: float = 0.7):
    return self.repository.find_similar(smiles, min_similarity)

  def substructure_search(self, smiles: str):
    return self.repository.substructure_search(smiles)
