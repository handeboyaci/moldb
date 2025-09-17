import uuid
from unittest.mock import Mock

import pytest
from rdkit import Chem

from src.app.models.molecule import Molecule
from src.app.repositories.molecule_repository import MoleculeRepository


@pytest.fixture(scope="function")
def mock_redis_client():
  mock = Mock()
  mock.get.return_value = None
  return mock


@pytest.fixture(scope="function")
def repository(db_session, mock_redis_client):
  return MoleculeRepository(db_session, mock_redis_client)


def test_search_no_filters(repository, db_session):
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles=mol1_smiles,
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  mol2_smiles = "CCC"
  mol2_mol = Chem.MolFromSmiles(mol2_smiles)
  mol2_fp = repository.fpgen.GetFingerprint(mol2_mol)
  mol2 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
    inchi="inchi2",
    inchikey="inchikey2",
    smiles=mol2_smiles,
    mol=mol2_mol,
    molecular_weight=44.1,
    chemical_formula="C3H8",
    logp=1.4,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=1,
    morgan_fingerprint=mol2_fp,
  )
  db_session.add_all([mol1, mol2])
  db_session.flush()

  molecules = repository.search()
  assert len(molecules) == 2


def test_search_with_min_mol_weight(repository, db_session):
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles=mol1_smiles,
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  mol2_smiles = "CCC"
  mol2_mol = Chem.MolFromSmiles(mol2_smiles)
  mol2_fp = repository.fpgen.GetFingerprint(mol2_mol)
  mol2 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
    inchi="inchi2",
    inchikey="inchikey2",
    smiles=mol2_smiles,
    mol=mol2_mol,
    molecular_weight=44.1,
    chemical_formula="C3H8",
    logp=1.4,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=1,
    morgan_fingerprint=mol2_fp,
  )
  db_session.add_all([mol1, mol2])
  db_session.flush()
  molecules = repository.search(min_mol_weight=45)
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"


def test_search_with_max_mol_weight(repository, db_session):
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles=mol1_smiles,
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  mol2_smiles = "CCC"
  mol2_mol = Chem.MolFromSmiles(mol2_smiles)
  mol2_fp = repository.fpgen.GetFingerprint(mol2_mol)
  mol2 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
    inchi="inchi2",
    inchikey="inchikey2",
    smiles=mol2_smiles,
    mol=mol2_mol,
    molecular_weight=44.1,
    chemical_formula="C3H8",
    logp=1.4,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=1,
    morgan_fingerprint=mol2_fp,
  )
  db_session.add_all([mol1, mol2])
  db_session.flush()
  molecules = repository.search(max_mol_weight=45)
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCC"


def test_find_similar(repository, db_session):
  # Add test data
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles=mol1_smiles,  # Ethanol
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  mol2_smiles = "CCN"
  mol2_mol = Chem.MolFromSmiles(mol2_smiles)
  mol2_fp = repository.fpgen.GetFingerprint(mol2_mol)
  mol2 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
    inchi="inchi2",
    inchikey="inchikey2",
    smiles=mol2_smiles,  # Ethylamine
    mol=mol2_mol,
    molecular_weight=45.08,
    chemical_formula="C2H7N",
    logp=0.03,
    tpsa=26.02,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=1,
    morgan_fingerprint=mol2_fp,
  )
  mol3_smiles = "C1CCCCC1"
  mol3_mol = Chem.MolFromSmiles(mol3_smiles)
  mol3_fp = repository.fpgen.GetFingerprint(mol3_mol)
  mol3 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
    inchi="inchi3",
    inchikey="inchikey3",
    smiles=mol3_smiles,  # Cyclohexane
    mol=mol3_mol,
    molecular_weight=84.16,
    chemical_formula="C6H12",
    logp=3.44,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=0,
    morgan_fingerprint=mol3_fp,
  )
  db_session.add_all([mol1, mol2, mol3])
  db_session.flush()

  # Search for molecules similar to Ethanol
  similar_molecules_result = repository.find_similar(smiles="CCO", min_similarity=0.1)

  assert len(similar_molecules_result.results) > 0
  # The most similar molecule should be ethanol itself
  assert similar_molecules_result.results[0].smiles == "CCO"
  assert hasattr(similar_molecules_result.results[0], "similarity_score")
  # The similarity of a molecule with itself is 1.0
  assert similar_molecules_result.results[0].similarity_score == 1.0


def test_substructure_search(repository, db_session):
  # Add test data
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles=mol1_smiles,  # Ethanol
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  mol2_smiles = "CCN"
  mol2_mol = Chem.MolFromSmiles(mol2_smiles)
  mol2_fp = repository.fpgen.GetFingerprint(mol2_mol)
  mol2 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
    inchi="inchi2",
    inchikey="inchikey2",
    smiles=mol2_smiles,  # Ethylamine
    mol=mol2_mol,
    molecular_weight=45.08,
    chemical_formula="C2H7N",
    logp=0.03,
    tpsa=26.02,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=1,
    morgan_fingerprint=mol2_fp,
  )
  mol3_smiles = "C1CCCCC1"
  mol3_mol = Chem.MolFromSmiles(mol3_smiles)
  mol3_fp = repository.fpgen.GetFingerprint(mol3_mol)
  mol3 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
    inchi="inchi3",
    inchikey="inchikey3",
    smiles=mol3_smiles,  # Cyclohexane
    mol=mol3_mol,
    molecular_weight=84.16,
    chemical_formula="C6H12",
    logp=3.44,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=0,
    morgan_fingerprint=mol3_fp,
  )
  db_session.add_all([mol1, mol2, mol3])
  db_session.flush()

  # Search for molecules containing the 'CC' substructure
  results = repository.substructure_search(smiles="CC")

  assert len(results) == 3
  assert "CCO" in [m.smiles for m in results]
  assert "CCN" in [m.smiles for m in results]


def test_search_with_multiple_filters(repository, db_session):
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="inchi1",
    inchikey="inchikey1",
    smiles=mol1_smiles,
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  mol2_smiles = "CCC"
  mol2_mol = Chem.MolFromSmiles(mol2_smiles)
  mol2_fp = repository.fpgen.GetFingerprint(mol2_mol)
  mol2 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a12"),
    inchi="inchi2",
    inchikey="inchikey2",
    smiles=mol2_smiles,
    mol=mol2_mol,
    molecular_weight=44.1,
    chemical_formula="C3H8",
    logp=1.4,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=1,
    morgan_fingerprint=mol2_fp,
  )
  mol3_smiles = "C1CCCCC1"
  mol3_mol = Chem.MolFromSmiles(mol3_smiles)
  mol3_fp = repository.fpgen.GetFingerprint(mol3_mol)
  mol3 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
    inchi="inchi3",
    inchikey="inchikey3",
    smiles=mol3_smiles,
    mol=mol3_mol,
    molecular_weight=84.16,
    chemical_formula="C6H12",
    logp=3.44,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=0,
    morgan_fingerprint=mol3_fp,
  )
  db_session.add_all([mol1, mol2, mol3])
  db_session.flush()

  # Test with multiple filters: min_mol_weight and max_logp
  molecules = repository.search(min_mol_weight=45, max_logp=0.0)
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"

  # Test with min_tpsa and max_h_bond_donors
  molecules = repository.search(min_tpsa=10, max_h_bond_donors=1)
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"


def test_search_with_chemical_identifiers(repository, db_session):
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = repository.fpgen.GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
    inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
    smiles=mol1_smiles,
    mol=mol1_mol,
    molecular_weight=46.07,
    chemical_formula="C2H6O",
    logp=-0.31,
    tpsa=20.23,
    h_bond_donors=1,
    h_bond_acceptors=1,
    rotatable_bonds=0,
    morgan_fingerprint=mol1_fp,
  )
  db_session.add(mol1)
  db_session.flush()

  # Search by InChI
  molecules = repository.search(inchi="InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3")
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"

  # Search by InChIKey
  molecules = repository.search(inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N")
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"

  # Search by SMILES
  molecules = repository.search(smiles="CCO")
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"

  # Search by Chemical Formula
  molecules = repository.search(chemical_formula="C2H6O")
  assert len(molecules) == 1
  assert molecules[0].smiles == "CCO"

  # Search by non-existent identifier
  molecules = repository.search(inchi="non-existent-inchi")
  assert len(molecules) == 0
