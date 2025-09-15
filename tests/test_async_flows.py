import time


def test_create_molecule_async_flow(client):
  # 1. Enqueue the job
  response = client.post("/api/v1/molecule", json={"smiles": "CCO"})
  assert response.status_code == 202
  job_id = response.json()["job_id"]
  assert job_id is not None

  # 2. Poll for the result
  result = None
  for _ in range(20):  # Poll for a maximum of 20 seconds
    response = client.get(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 200
    data = response.json()
    if data["status"] == "finished":
      result = data["result"]
      break
    time.sleep(1)

  # 3. Assert the final result
  assert result is not None
  assert result["smiles"] == "CCO"
  assert result["molecular_weight"] == 46.069
