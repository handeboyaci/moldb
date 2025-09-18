import gzip
import os
import sys
import time

import requests
from requests.exceptions import ConnectionError
from requests.exceptions import RequestException

# Add the parent directory to the Python path to allow imports from src.app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CHEMBL_DATA_URL = "http://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/chembl_23/chembl_23_chemreps.txt.gz"
GZ_FILE_PATH = "/app/uploads/chembl_23_chemreps.txt.gz"
API_URL = "http://app:8000/api/v1/ingest"
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
    except RequestException as e:
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
    except ConnectionError:
      pass
    print("API not yet healthy, retrying...")
    time.sleep(interval)
  print("API did not become healthy within the timeout period.")
  return False


def insert_data_via_api():
  SMILES_FILE_PATH = "/app/uploads/chembl_23_smiles.txt"

  if not wait_for_api_health(HEALTH_CHECK_URL):
    print("Cannot insert data: API is not healthy.")
    sys.exit(1)

  download_chembl_data()

  if not os.path.exists(GZ_FILE_PATH):
    print("ChEMBL data file not available. Skipping data insertion.")
    return

  print(f"Processing {GZ_FILE_PATH} to extract SMILES...")
  try:
    with (
      gzip.open(GZ_FILE_PATH, "rt", encoding="utf-8") as gz_f,
      open(SMILES_FILE_PATH, "w", encoding="utf-8") as smiles_f,
    ):
      # Skip header
      gz_f.readline()
      for line in gz_f:
        parts = line.strip().split("\t")
        if len(parts) > 1:
          smiles_f.write(parts[1] + "\n")
    print(f"SMILES extracted to {SMILES_FILE_PATH}.")
  except Exception as e:
    print(f"Error processing gzipped file: {e}")
    sys.exit(1)

  print(f"Initiating ingestion for {SMILES_FILE_PATH} via API...")

  try:
    response = requests.post(API_URL, json={"file_path": SMILES_FILE_PATH[13:]})
    response.raise_for_status()  # Raise an exception for HTTP errors
    print(f"Successfully initiated ingestion for {SMILES_FILE_PATH}.")
  except RequestException as e:
    print(f"Error initiating ingestion for {SMILES_FILE_PATH}: {e}")
    sys.exit(1)


if __name__ == "__main__":
  insert_data_via_api()
