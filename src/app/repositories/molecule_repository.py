import json
from uuid import UUID

import redis
from rdkit import Chem
from rdkit.Chem import AllChem
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..models.molecule import (
  Molecule,
  MoleculeInDB,
  MoleculeOut,
  MoleculeWithSimilarity,
  SimilaritySearchResults,
)


class MoleculeRepository:
  def __init__(self, db: Session, redis_client: redis.Redis):
    self.db = db
    self.redis_client = redis_client

  def create_molecule(self, molecule: MoleculeInDB):
    db_molecule = Molecule(**molecule.model_dump())
    self.db.add(db_molecule)
    self.db.commit()
    self.db.refresh(db_molecule)
    return MoleculeOut.model_validate(db_molecule)

  def bulk_insert_molecules(self, molecules: list[MoleculeInDB]):
    if not molecules:
      return

    molecule_mappings = [m.model_dump() for m in molecules]
    self.db.bulk_insert_mappings(Molecule, molecule_mappings)
    self.db.commit()

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

  def find_similar(self, smiles: str, min_similarity: float, force_recompute: bool = False) -> SimilaritySearchResults:
    query_mol = Chem.MolFromSmiles(smiles)
    if query_mol is None:
      return SimilaritySearchResults(cache_hit=False, results=[])

    inchikey = AllChem.MolToInchiKey(query_mol)
    cache_key = f"similarity:{inchikey}:{min_similarity:.2f}"

    if not force_recompute:
      cached_results = self.redis_client.get(cache_key)
      if cached_results:
        results_json = json.loads(cached_results)
        results = [MoleculeWithSimilarity.model_validate(res) for res in results_json]
        return SimilaritySearchResults(cache_hit=True, results=results)

    sql = text("""
        SELECT
            id,
            smiles,
            molecular_weight,
            logp,
            tpsa,
            h_bond_donors,
            h_bond_acceptors,
            rotatable_bonds,
            inchi,
            inchikey,
            chemical_formula,
            tanimoto_sml(morgan_fingerprint::bfp, morganbv_fp(mol_from_smiles(:smiles))) as similarity_score
        FROM molecules
        WHERE morgan_fingerprint::bfp % morganbv_fp(mol_from_smiles(:smiles))
        AND tanimoto_sml(morgan_fingerprint::bfp, morganbv_fp(mol_from_smiles(:smiles))) >= :min_similarity
        ORDER BY similarity_score DESC;
    """)

    result = self.db.execute(sql, {"smiles": smiles, "min_similarity": min_similarity})

    similar_molecules = []
    for row in result:
      mol_data = {
        "id": row.id,
        "smiles": row.smiles,
        "molecular_weight": row.molecular_weight,
        "logp": row.logp,
        "tpsa": row.tpsa,
        "h_bond_donors": row.h_bond_donors,
        "h_bond_acceptors": row.h_bond_acceptors,
        "rotatable_bonds": row.rotatable_bonds,
        "inchi": row.inchi,
        "inchikey": row.inchikey,
        "chemical_formula": row.chemical_formula,
        "similarity_score": row.similarity_score,
      }
      similar_molecules.append(MoleculeWithSimilarity.model_validate(mol_data))

    similar_molecules.sort(key=lambda x: x.similarity_score, reverse=True)

    # Serialize for caching
    results_to_cache = [res.model_dump() for res in similar_molecules]
    self.redis_client.set(cache_key, json.dumps(results_to_cache, default=str), ex=3600)  # 1 hour expiration

    return SimilaritySearchResults(cache_hit=False, results=similar_molecules)

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
