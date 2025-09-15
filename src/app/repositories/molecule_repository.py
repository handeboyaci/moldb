from uuid import UUID

from rdkit import Chem, DataStructs
from rdkit.Chem import rdMolDescriptors
from sqlalchemy.orm import Session

from ..models.molecule import Molecule, MoleculeInDB, MoleculeOut


class MoleculeRepository:
  def __init__(self, db: Session):
    self.db = db

  def create_molecule(self, molecule: MoleculeInDB):
    db_molecule = Molecule(**molecule.model_dump())
    self.db.add(db_molecule)
    self.db.commit()
    self.db.refresh(db_molecule)
    return MoleculeOut.model_validate(db_molecule)

  def search(
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
    query = self.db.query(Molecule)
    if min_mol_weight is not None:
      query = query.filter(Molecule.molecular_weight >= min_mol_weight)
    if max_mol_weight is not None:
      query = query.filter(Molecule.molecular_weight <= max_mol_weight)
    if min_logp is not None:
      query = query.filter(Molecule.logp >= min_logp)
    if max_logp is not None:
      query = query.filter(Molecule.logp <= max_logp)
    if min_tpsa is not None:
      query = query.filter(Molecule.tpsa >= min_tpsa)
    if max_tpsa is not None:
      query = query.filter(Molecule.tpsa <= max_tpsa)
    if min_h_bond_donors is not None:
      query = query.filter(Molecule.h_bond_donors >= min_h_bond_donors)
    if max_h_bond_donors is not None:
      query = query.filter(Molecule.h_bond_donors <= max_h_bond_donors)
    if min_h_bond_acceptors is not None:
      query = query.filter(Molecule.h_bond_acceptors >= min_h_bond_acceptors)
    if max_h_bond_acceptors is not None:
      query = query.filter(Molecule.h_bond_acceptors <= max_h_bond_acceptors)
    if min_rotatable_bonds is not None:
      query = query.filter(Molecule.rotatable_bonds >= min_rotatable_bonds)
    if max_rotatable_bonds is not None:
      query = query.filter(Molecule.rotatable_bonds <= max_rotatable_bonds)
    if inchi is not None:
      query = query.filter(Molecule.inchi == inchi)
    if inchikey is not None:
      query = query.filter(Molecule.inchikey == inchikey)
    if smiles is not None:
      query = query.filter(Molecule.smiles == smiles)
    if chemical_formula is not None:
      query = query.filter(Molecule.chemical_formula == chemical_formula)
    return query.all()

  def find_by_id(self, molecule_id: UUID):
    return self.db.query(Molecule).filter(Molecule.id == molecule_id).first()

  def find_similar(self, smiles: str, min_similarity: float):
    query_mol = Chem.MolFromSmiles(smiles)
    if query_mol is None:
      return []
    query_fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(query_mol, 2, nBits=2048)

    similar_molecules = []
    all_molecules = self.db.query(Molecule).all()

    for mol_in_db in all_molecules:
      if mol_in_db.mol is not None:
        db_fp = rdMolDescriptors.GetMorganFingerprintAsBitVect(mol_in_db.mol, 2, nBits=2048)
        similarity = DataStructs.TanimotoSimilarity(query_fp, db_fp)
        if similarity >= min_similarity:
          mol_in_db.similarity_score = similarity
          similar_molecules.append(mol_in_db)

    similar_molecules.sort(key=lambda x: x.similarity_score, reverse=True)
    return similar_molecules

  def substructure_search(self, smiles: str):
    query_substructure = Chem.MolFromSmiles(smiles)
    if query_substructure is None:
      return []

    matching_molecules = []
    all_molecules = self.db.query(Molecule).all()

    for mol_in_db in all_molecules:
      if mol_in_db.mol is not None and mol_in_db.mol.HasSubstructMatch(query_substructure):
        matching_molecules.append(mol_in_db)
    return matching_molecules
