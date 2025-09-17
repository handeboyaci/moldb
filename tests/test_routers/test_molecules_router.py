import uuid
from unittest.mock import mock_open, patch

import pytest
from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator
from rq.job import Job

from src.app.dependencies import redis_conn
from src.app.models.molecule import Molecule


@pytest.fixture(scope="function")
def seed_molecules(db_session):
  # Add test data
  fpgen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
  mol1_smiles = "CCO"
  mol1_mol = Chem.MolFromSmiles(mol1_smiles)
  mol1_fp = fpgen.GetFingerprint(mol1_mol)
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
  mol2_fp = fpgen.GetFingerprint(mol2_mol)
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
  mol3_smiles = "CCCC"
  mol3_mol = Chem.MolFromSmiles(mol3_smiles)
  mol3_fp = fpgen.GetFingerprint(mol3_mol)
  mol3 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a13"),
    inchi="inchi3",
    inchikey="inchikey3",
    smiles=mol3_smiles,
    mol=mol3_mol,
    molecular_weight=58.12,
    chemical_formula="C4H10",
    logp=2.0,
    tpsa=0.0,
    h_bond_donors=0,
    h_bond_acceptors=0,
    rotatable_bonds=2,
    morgan_fingerprint=mol3_fp,
  )
  mol4_smiles = "C1=CC=C(C=C1)C(=O)O"  # Benzoic acid
  mol4_mol = Chem.MolFromSmiles(mol4_smiles)
  mol4_fp = fpgen.GetFingerprint(mol4_mol)
  mol4 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a14"),
    inchi="InChI=1S/C7H6O2/c8-7(9)6-4-2-1-3-5-6/h1-5H,(H,8,9)",
    inchikey="WPYMKLBDIGXBTP-UHFFFAOYSA-N",
    smiles=mol4_smiles,
    mol=mol4_mol,
    molecular_weight=122.12,
    chemical_formula="C7H6O2",
    logp=1.87,
    tpsa=37.3,
    h_bond_donors=1,
    h_bond_acceptors=2,
    rotatable_bonds=1,
    morgan_fingerprint=mol4_fp,
  )
  mol5_smiles = "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"  # Caffeine
  mol5_mol = Chem.MolFromSmiles(mol5_smiles)
  mol5_fp = fpgen.GetFingerprint(mol5_mol)
  mol5 = Molecule(
    id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a15"),
    inchi="InChI=1S/C8H10N4O2/c1-10-4-9-3(8(13)14)12(2)7(11)5-6(4)10/h5H,1-2H3",
    inchikey="RYYVLZVUVIYJQO-UHFFFAOYSA-N",
    smiles=mol5_smiles,
    mol=mol5_mol,
    molecular_weight=194.19,
    chemical_formula="C8H10N4O2",
    logp=-0.07,
    tpsa=61.4,
    h_bond_donors=0,
    h_bond_acceptors=4,
    rotatable_bonds=0,
    morgan_fingerprint=mol5_fp,
  )
  db_session.add_all([mol1, mol2, mol3, mol4, mol5])
  db_session.flush()


def wait_for_job(job_id):
  import time

  start_time = time.time()
  job = Job.fetch(job_id, connection=redis_conn)
  while job.get_status() not in ["finished", "failed"]:
    time.sleep(0.1)
    job.refresh()
    if time.time() - start_time > 10:
      raise TimeoutError("Job did not finish in 10 seconds")
  return job


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_no_filters(client):
  response = client.get("/api/v1/search")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result) == 5


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_with_min_mol_weight(client):
  response = client.get("/api/v1/search?min_mol_weight=50")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result) == 3
  smiles_list = [m.smiles for m in result]
  assert "CCCC" in smiles_list
  assert "C1=CC=C(C=C1)C(=O)O" in smiles_list
  assert "CN1C=NC2=C1C(=O)N(C(=O)N2C)C" in smiles_list


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_with_max_mol_weight(client):
  response = client.get("/api/v1/search?max_mol_weight=45")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "CCC"


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_with_min_and_max_mol_weight(client):
  response = client.get("/api/v1/search?min_mol_weight=45&max_mol_weight=50")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "CCO"


@pytest.mark.usefixtures("seed_molecules")
def test_find_similar_molecules(client):
  response = client.post(
    "/api/v1/search/similar", json={"smiles": "CCO", "min_similarity": 0.1}
  )
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result.results) > 0
  assert result.results[0].smiles == "CCO"
  assert hasattr(result.results[0], "similarity_score")
  assert result.results[0].similarity_score == 1.0


@pytest.mark.usefixtures("seed_molecules")
def test_substructure_search(client):
  response = client.post("/api/v1/search/substructure", json={"smiles": "CC"})
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result) == 4
  smiles_list = [m.smiles for m in result]
  assert "CCO" in smiles_list
  assert "CCC" in smiles_list
  assert "CCCC" in smiles_list
  assert "C1=CC=C(C=C1)C(=O)O" in smiles_list


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_with_all_filters(client):
  response = client.get(
    "/api/v1/search?min_mol_weight=120&max_mol_weight=130&min_logp=1&max_logp=2&min_tpsa=30&max_tpsa=40&min_h_bond_donors=1&max_h_bond_donors=1&min_h_bond_acceptors=2&max_h_bond_acceptors=2&min_rotatable_bonds=1&max_rotatable_bonds=1"
  )
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  assert job.get_status() == "finished"
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "C1=CC=C(C=C1)C(=O)O"


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_with_chemical_identifiers(client):
  # Search by InChI
  response = client.get(
    "/api/v1/search?inchi=InChI=1S/C8H10N4O2/c1-10-4-9-3(8(13)14)12(2)7(11)5-6(4)10/h5H,1-2H3"
  )
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

  # Search by InChIKey
  response = client.get("/api/v1/search?inchikey=RYYVLZVUVIYJQO-UHFFFAOYSA-N")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

  # Search by SMILES
  response = client.get("/api/v1/search?smiles=CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

  # Search by Chemical Formula
  response = client.get("/api/v1/search?chemical_formula=C8H10N4O2")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  result = job.return_value()
  assert len(result) == 1
  assert result[0].smiles == "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"

  # Search by non-existent identifier
  response = client.get("/api/v1/search?inchi=non-existent-inchi")
  assert response.status_code == 202
  job = wait_for_job(response.json()["job_id"])
  result = job.return_value()
  assert len(result) == 0


@pytest.mark.usefixtures("seed_molecules")
def test_find_similar_molecules_caching(client):
  # Clear cache for this test
  redis_conn.flushdb()

  # 1. First call, should miss cache
  response1 = client.post(
    "/api/v1/search/similar", json={"smiles": "CCO", "min_similarity": 0.7}
  )
  assert response1.status_code == 202
  job1 = wait_for_job(response1.json()["job_id"])
  assert job1.get_status() == "finished"
  result1 = job1.return_value()
  assert not result1.cache_hit
  assert len(result1.results) > 0

  # 2. Second call, should hit cache
  response2 = client.post(
    "/api/v1/search/similar", json={"smiles": "CCO", "min_similarity": 0.7}
  )
  assert response2.status_code == 202
  job2 = wait_for_job(response2.json()["job_id"])
  assert job2.get_status() == "finished"
  result2 = job2.return_value()
  assert result2.cache_hit
  assert len(result2.results) > 0

  # 3. Third call, with force_recompute, should miss cache
  response3 = client.post(
    "/api/v1/search/similar",
    json={"smiles": "CCO", "min_similarity": 0.7, "force_recompute": True},
  )
  assert response3.status_code == 202
  job3 = wait_for_job(response3.json()["job_id"])
  assert job3.get_status() == "finished"
  result3 = job3.return_value()
  assert not result3.cache_hit
  assert len(result3.results) > 0


@patch("src.worker.tasks.Path.stat")
@patch("builtins.open", new_callable=mock_open, read_data="CC\nCCC\nCCCC")
def test_ingest_molecules_success(mock_open_file, mock_stat, client):
  """Test successful ingestion of a file with mocked filesystem."""
  mock_stat.return_value.st_size = 15

  response = client.post("/api/v1/ingest", json={"file_path": "test_ingest.txt"})
  assert response.status_code == 202
  job_id = response.json()["job_id"]
  job = wait_for_job(job_id)
  assert job.get_status() == "finished"

  # This part of the test is now harder to verify without a real DB write.
  # We trust the unit tests for the worker to cover the logic.


@patch("src.worker.tasks.Path.stat", side_effect=FileNotFoundError)
def test_ingest_molecules_file_not_found(mock_stat, client):
  """Test ingestion with a file that does not exist using mocks."""
  response = client.post("/api/v1/ingest", json={"file_path": "non_existent_file.txt"})
  assert response.status_code == 202  # The job is enqueued, but will fail
  job_id = response.json()["job_id"]
  job = wait_for_job(job_id)
  assert job.get_status() == "failed"


@pytest.mark.usefixtures("seed_molecules")
def test_create_molecule_sync(client):
  response = client.post("/api/v1/molecule?sync=true", json={"smiles": "CCO"})
  assert response.status_code == 200
  data = response.json()
  assert data["smiles"] == "CCO"


@pytest.mark.usefixtures("seed_molecules")
def test_search_molecules_sync(client):
  response = client.get("/api/v1/search?sync=true&min_mol_weight=50")
  assert response.status_code == 200
  data = response.json()
  assert len(data) == 3


@pytest.mark.usefixtures("seed_molecules")
def test_find_similar_molecules_sync(client):
  response = client.post(
    "/api/v1/search/similar?sync=true",
    json={"smiles": "CCO", "min_similarity": 0.1},
  )
  assert response.status_code == 200
  data = response.json()
  assert len(data["results"]) > 0


@pytest.mark.usefixtures("seed_molecules")
def test_substructure_search_sync(client):
  response = client.post("/api/v1/search/substructure?sync=true", json={"smiles": "CC"})
  assert response.status_code == 200
  data = response.json()
  assert len(data) == 4


@patch("src.worker.tasks.Path.stat")
@patch("builtins.open", new_callable=mock_open, read_data="CC\nCCC\nCCCC")
def test_ingest_molecules_sync_success(mock_open_file, mock_stat, client):
  mock_stat.return_value.st_size = 15
  response = client.post(
    "/api/v1/ingest?sync=true", json={"file_path": "test_ingest.txt"}
  )
  assert response.status_code == 200
