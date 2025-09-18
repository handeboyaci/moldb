import json
import uuid
from unittest.mock import Mock

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem import rdFingerprintGenerator

from src.app.models.molecule import Molecule
from src.app.models.molecule import MoleculeWithSimilarity
from src.app.repositories.molecule_repository import MoleculeRepository


@pytest.fixture(scope="function")
def mock_redis_client():
  mock_client = Mock()
  mock_client.get.return_value = None
  return mock_client


@pytest.fixture(scope="function")
def repository(db_session, mock_redis_client):
  return MoleculeRepository(db_session, mock_redis_client)


@pytest.fixture(scope="function")
def db_with_data(db_session):
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)

  mol1_fp = rdFingerprintGenerator.GetMorganGenerator(
    radius=2, fpSize=2048
  ).GetFingerprint(mol1_mol)
  mol1 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
    inchi="InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
    inchikey="LFQSCWFLJHTTHZ-UHFFFAOYSA-N",
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
  db_session.add(mol1)
  db_session.commit()
  return db_session


def test_find_similar_caching_flow(repository, db_with_data, mock_redis_client):
  smiles = "CCO"
  min_similarity = 0.7

  # 1. First call, should miss cache
  result1 = repository.find_similar(smiles, min_similarity)

  assert not result1.cache_hit
  assert len(result1.results) == 1
  assert result1.results[0].smiles == "CCO"

  # Verify cache was set
  query_mol = Chem.MolFromSmiles(smiles)
  inchikey = AllChem.MolToInchiKey(query_mol)
  cache_key = f"similarity:{inchikey}:{min_similarity:.2f}"
  mock_redis_client.set.assert_called_once()
  args, kwargs = mock_redis_client.set.call_args
  assert args[0] == cache_key
  assert "ex" in kwargs

  # 2. Setup mock to return cached value
  cached_data = [res.model_dump() for res in result1.results]
  mock_redis_client.get.return_value = json.dumps(cached_data, default=str)

  # 3. Second call, should hit cache
  result2 = repository.find_similar(smiles, min_similarity)

  assert result2.cache_hit
  assert len(result2.results) == 1
  assert result2.results[0].smiles == "CCO"
  # Ensure DB was not hit again (in this test, we can't easily check if the DB was hit,
  # but we check that get was called)
  mock_redis_client.get.assert_called_with(cache_key)


def test_find_similar_force_recompute(repository, db_with_data, mock_redis_client):
  smiles = "CCO"
  min_similarity = 0.7

  # Setup mock to return a cached value
  mock_result = MoleculeWithSimilarity(
    id=uuid.uuid4(),
    inchi="fake-inchi",
    inchikey="FAKE-INCHIKEY",
    smiles="FAKECCO",
    molecular_weight=0,
    chemical_formula="",
    logp=0,
    tpsa=0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=0,
    similarity_score=0.99,
  )
  cached_data = [mock_result.model_dump()]
  mock_redis_client.get.return_value = json.dumps(cached_data, default=str)

  # Call with force_recompute = True
  result = repository.find_similar(smiles, min_similarity, force_recompute=True)

  # Verify cache was not used and result is from DB
  assert not result.cache_hit
  assert len(result.results) == 1
  assert result.results[0].smiles == "CCO"

  # Verify get was not called
  mock_redis_client.get.assert_not_called()
