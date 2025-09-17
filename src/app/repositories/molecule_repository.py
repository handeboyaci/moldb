import json
from uuid import UUID

import redis
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem, rdFingerprintGenerator
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
    self.fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)

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
    skip: int = 0,
    limit: int = 100,
  ) -> list[MoleculeOut]:
    query = self.db.query(Molecule)
    filters = []
    if min_mol_weight is not None:
      filters.append(Molecule.molecular_weight >= min_mol_weight)
    if max_mol_weight is not None:
      filters.append(Molecule.molecular_weight <= max_mol_weight)
    if min_logp is not None:
      filters.append(Molecule.logp >= min_logp)
    if max_logp is not None:
      filters.append(Molecule.logp <= max_logp)
    if min_tpsa is not None:
      filters.append(Molecule.tpsa >= min_tpsa)
    if max_tpsa is not None:
      filters.append(Molecule.tpsa <= max_tpsa)
    if min_h_bond_donors is not None:
      filters.append(Molecule.h_bond_donors >= min_h_bond_donors)
    if max_h_bond_donors is not None:
      filters.append(Molecule.h_bond_donors <= max_h_bond_donors)
    if min_h_bond_acceptors is not None:
      filters.append(Molecule.h_bond_acceptors >= min_h_bond_acceptors)
    if max_h_bond_acceptors is not None:
      filters.append(Molecule.h_bond_acceptors <= max_h_bond_acceptors)
    if min_rotatable_bonds is not None:
      filters.append(Molecule.rotatable_bonds >= min_rotatable_bonds)
    if max_rotatable_bonds is not None:
      filters.append(Molecule.rotatable_bonds <= max_rotatable_bonds)
    if inchi is not None:
      filters.append(Molecule.inchi == inchi)
    if inchikey is not None:
      filters.append(Molecule.inchikey == inchikey)
    if smiles is not None:
      filters.append(Molecule.smiles == smiles)
    if chemical_formula is not None:
      filters.append(Molecule.chemical_formula == chemical_formula)

    if filters:
      query = query.filter(*filters)

    results = query.offset(skip).limit(limit).all()
    return [MoleculeOut.model_validate(row) for row in results]

  def find_by_id(self, molecule_id: UUID) -> MoleculeOut | None:
    db_molecule = self.db.query(Molecule).filter(Molecule.id == molecule_id).first()
    if db_molecule:
      return MoleculeOut.model_validate(db_molecule)
    return None

  def find_by_inchikey(self, inchikey: str) -> MoleculeOut | None:
    db_molecule = self.db.query(Molecule).filter(Molecule.inchikey == inchikey).first()
    if db_molecule:
      return MoleculeOut.model_validate(db_molecule)
    return None

  def find_similar(
    self, smiles: str, min_similarity: float, force_recompute: bool = False
  ) -> SimilaritySearchResults:
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

    query_fp = DataStructs.BitVectToFPSText(self.fpgen.GetFingerprint(query_mol))

    sql = text(
      """
        SELECT
            m.id,
            m.smiles,
            m.molecular_weight,
            m.logp,
            m.tpsa,
            m.h_bond_donors,
            m.h_bond_acceptors,
            m.rotatable_bonds,
            m.inchi,
            m.inchikey,
            m.chemical_formula,
            tanimoto_sml(
                m.morgan_fingerprint, bfp_from_binary_text(:query_fp)
            ) AS similarity_score
        FROM
            molecules m
        WHERE
            m.morgan_fingerprint % bfp_from_binary_text(:query_fp)
            AND tanimoto_sml(
                m.morgan_fingerprint, bfp_from_binary_text(:query_fp)
            ) >= :min_similarity
        ORDER BY
            similarity_score DESC;
        """
    )

    result = self.db.execute(
      sql,
      {
        "query_fp": query_fp,
        "min_similarity": min_similarity,
      },
    )

    similar_molecules = [
      MoleculeWithSimilarity.model_validate(row, from_attributes=True) for row in result
    ]

    # Serialize for caching
    results_to_cache = [res.model_dump() for res in similar_molecules]
    self.redis_client.set(
      cache_key, json.dumps(results_to_cache, default=str), ex=3600
    )  # 1 hour expiration

    return SimilaritySearchResults(cache_hit=False, results=similar_molecules)

  def substructure_search(self, smiles: str, skip: int = 0, limit: int = 100):
    sql = text(
      """
        SELECT
            id, inchi, inchikey, smiles, molecular_weight, chemical_formula, logp,
            tpsa, h_bond_donors, h_bond_acceptors, rotatable_bonds
        FROM molecules
        WHERE mol @> mol_from_smiles(:smiles)
        OFFSET :skip
        LIMIT :limit;
    """
    )
    result = self.db.execute(sql, {"smiles": smiles, "skip": skip, "limit": limit})
    return [MoleculeOut.model_validate(row, from_attributes=True) for row in result]
