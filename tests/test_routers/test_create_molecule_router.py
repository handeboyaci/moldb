def test_create_molecule_success(client, context_aware_task_queue):
  response = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response.status_code == 202
  data = response.json()
  assert data["status"] == "finished"
  job = context_aware_task_queue.fetch_job(data["job_id"])
  assert job is not None
  result = job.return_value()
  assert result is not None
  assert result.smiles == "CCO"
  assert result.id is not None


def test_create_molecule_invalid_smiles(client, context_aware_task_queue):
  response = client.post("/api/v1/molecule", json={"smiles": "invalid-smiles"})
  assert response.status_code == 202
  data = response.json()
  assert data["status"] == "failed"
  job = context_aware_task_queue.fetch_job(data["job_id"])
  assert job is not None
  latest_result = job.latest_result()
  assert latest_result is not None
  assert isinstance(latest_result.exc_string, str)
  assert "Invalid SMILES string" in latest_result.exc_string


def test_create_molecule_duplicate_inchi(client, context_aware_task_queue):
  # First creation should succeed
  response1 = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response1.status_code == 202
  data1 = response1.json()
  assert data1["status"] == "finished"
  job1 = context_aware_task_queue.fetch_job(data1["job_id"])
  assert job1 is not None
  result1 = job1.return_value()
  assert result1 is not None
  assert result1.smiles == "CCO"

  # Second creation should also succeed and return the existing molecule
  response2 = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response2.status_code == 202
  data2 = response2.json()
  assert data2["status"] == "finished"
  job2 = context_aware_task_queue.fetch_job(data2["job_id"])
  assert job2 is not None
  result2 = job2.return_value()
  assert result2 is not None

  # Check that the returned molecule is the same one
  assert result2.id == result1.id


def test_create_molecule_missing_smiles(client):
  response = client.post("/api/v1/molecule", json={})
  assert response.status_code == 422  # Unprocessable Entity for validation errors
  data = response.json()
  assert "detail" in data
