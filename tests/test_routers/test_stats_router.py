import uuid
from unittest.mock import patch

from rdkit import Chem
from rdkit.Chem import rdFingerprintGenerator

from src.app.models.molecule import Molecule


def test_get_molecule_count(client, db_session):
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
  db_session.add_all([mol1, mol2])
  db_session.flush()

  response = client.get("/api/v1/stats/molecules/count")
  assert response.status_code == 200
  assert response.json() == {"count": 2}


def test_get_active_jobs(client):
  mock_jobs = [
    {
      "job_id": "job1",
      "description": "description1",
      "started_at": "2025-10-13T12:00:00",
      "meta": {},
    }
  ]
  with patch("src.app.routers.stats.JobService") as MockJobService:
    mock_service_instance = MockJobService.return_value
    mock_service_instance.get_active_jobs.return_value = mock_jobs

    response = client.get("/api/v1/stats/jobs/active")
    assert response.status_code == 200
    assert response.json() == mock_jobs
