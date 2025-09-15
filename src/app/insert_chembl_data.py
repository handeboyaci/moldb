import gzip
import os
import sys
import time

import requests

# Add the parent directory to the Python path to allow imports from src.app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CHEMBL_DATA_URL = "http://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_23/chembl_23_chemreps.txt.gz"
GZ_FILE_PATH = "/app/data/chembl_23_chemreps.txt.gz"
API_URL = "http://app:8000/api/v1/molecule"
HEALTH_CHECK_URL = "http://app:8000/health"


def download_chembl_data():
  if not os.path.exists(GZ_FILE_PATH):
    print(f"Downloading ChEMBL data from {CHEMBL_DATA_URL}...")
    try:
      response = requests.get(CHEMBL_DATA_URL, stream=True)
      response.raise_for_status()
      os.makedirs(os.path.dirname(GZ_FILE_PATH), exist_ok=True)
      with open(GZ_FILE_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
          f.write(chunk)
      print("Download complete.")
    except requests.exceptions.RequestException as e:
      print(f"Error downloading ChEMBL data: {e}")
      sys.exit(1)
  else:
    print(f"ChEMBL data already exists at {GZ_FILE_PATH}. Skipping download.")


def wait_for_api_health(url, timeout=60, interval=1):
  print(f"Waiting for API to be healthy at {url}...")
  start_time = time.time()
  while time.time() - start_time < timeout:
    try:
      response = requests.get(url)
      if response.status_code == 200 and response.json().get("status") == "ok":
        print("API is healthy.")
        return True
    except requests.exceptions.ConnectionError:
      pass
    print("API not yet healthy, retrying...")
    time.sleep(interval)
  print("API did not become healthy within the timeout period.")
  return False


def insert_data_via_api():
  if not wait_for_api_health(HEALTH_CHECK_URL):
    print("Cannot insert data: API is not healthy.")
    sys.exit(1)

  download_chembl_data()

  if not os.path.exists(GZ_FILE_PATH):
    print("ChEMBL data file not available. Skipping data insertion.")
    return

  print(f"Inserting data from {GZ_FILE_PATH} into chemstructdb via API...")

  inserted_count = failed_count = 0
  with gzip.open(GZ_FILE_PATH, "rt") as f:
    header = f.readline().strip().split("\t")
    smiles_idx = header.index("canonical_smiles")

    for line in f:
      parts = line.strip().split("\t")
      if len(parts) != len(header):
        print(f"Skipping malformed line: {line.strip()}")
        continue

      smiles = parts[smiles_idx]

      try:
        response = requests.post(API_URL, json={"smiles": smiles})
        response.raise_for_status()  # Raise an exception for HTTP errors
        inserted_count += 1
        if inserted_count % 100 == 0:  # Print every molecule for testing
          print(f"Inserted {inserted_count} molecules...")

      except requests.exceptions.RequestException as e:
        failed_count += 1
        print(f"Error inserting molecule with SMILES {smiles}: {e}. Skipping.")

  print(f"Finished data insertion. Total {inserted_count} molecules inserted, {failed_count} failed.")


if __name__ == "__main__":
  insert_data_via_api()
