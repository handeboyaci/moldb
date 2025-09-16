from rq.job import Job

from src.app.dependencies import redis_conn


def test_create_molecule_success(client):
  response = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response.status_code == 202
  data = response.json()
  assert data["status"] == "finished"
  job = Job.fetch(data["job_id"], connection=redis_conn)
  result = job.return_value()
  assert result.smiles == "CCO"
  assert result.id is not None


def test_create_molecule_invalid_smiles(client):
  response = client.post("/api/v1/molecule", json={"smiles": "invalid-smiles"})
  assert response.status_code == 202
  data = response.json()
  assert data["status"] == "failed"
  job = Job.fetch(data["job_id"], connection=redis_conn)
  assert isinstance(job.latest_result().exc_string, str)
  assert "Invalid SMILES string" in job.latest_result().exc_string


def test_create_molecule_duplicate_inchi(client):
  # First creation should succeed
  response1 = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response1.status_code == 202
  assert response1.json()["status"] == "finished"

  # Second creation should fail
  response2 = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response2.status_code == 202
  data = response2.json()
  assert data["status"] == "failed"
  job = Job.fetch(data["job_id"], connection=redis_conn)
  assert "IntegrityError" in job.latest_result().exc_string


def test_create_molecule_missing_smiles(client):
  response = client.post("/api/v1/molecule", json={})
  assert response.status_code == 422  # Unprocessable Entity for validation errors
  data = response.json()
  assert "detail" in data
